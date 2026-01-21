from datetime import datetime
from typing import List, Optional
from enum import Enum as PyEnum
from sqlalchemy import (
    select,
    String,
    Integer,
    ForeignKey,
    Text,
    DECIMAL,
    DateTime,
    func,
    Boolean,
    Enum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel

from .database import Base, get_db
from .auth import get_current_user, get_verified_client, get_verified_worker
from .user import User, UserRole

router = APIRouter(prefix="/jobs", tags=["jobs"])


# === MODELS ===
class JobStatus(str, PyEnum):
    open = "open"
    closed = "closed"

class JobApplicationStatus(str, PyEnum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


class JobOffer(Base):
    __tablename__ = "job_offers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), index=True)
    location: Mapped[str] = mapped_column(String(100), index=True)
    budget_min: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2), nullable=True)
    budget_max: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2), nullable=True)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status"), default=JobStatus.open
    )
    boost_until: Mapped[Optional["DateTime"]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    client: Mapped["User"] = relationship(back_populates="job_offers")
    applications: Mapped[List["JobApplication"]] = relationship()


class JobApplication(Base):
    __tablename__ = "job_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("job_offers.id"), index=True)
    worker_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    cover_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[JobApplicationStatus] = mapped_column(
        Enum(JobApplicationStatus, name="application_status"), default=JobApplicationStatus.pending
    )

    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job: Mapped["JobOffer"] = relationship()
    worker: Mapped["User"] = relationship()


# === Pydantic Schemas ===
class JobOfferCreate(BaseModel):
    title: str
    description: str
    category: str
    location: str
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None


class JobOfferOut(BaseModel):
    id: int
    title: str
    description: str
    category: str
    location: str
    budget_min: Optional[float]
    budget_max: Optional[float]
    status: JobStatus
    boost_until: Optional[datetime]
    client_id: int
    created_at: datetime
    application_count: int  # computed


class JobApplicationCreate(BaseModel):
    cover_message: Optional[str] = None


class JobApplicationOut(BaseModel):
    id: int
    job_id: int
    worker_id: int
    cover_message: Optional[str]
    status: JobApplicationStatus
    created_at: datetime


# === ENDPOINTS ===
@router.post("", response_model=JobOfferOut, status_code=status.HTTP_201_CREATED)
async def create_job(
    data: JobOfferCreate,
    current_client: User = Depends(get_verified_client),
    db: AsyncSession = Depends(get_db),
):
    """Create job offer - VERIFIED CLIENTS ONLY"""
    job = JobOffer(
        client_id=current_client.id,
        **data.dict()
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Count applications (0 for new)
    result = await db.execute(select(func.count(JobApplication.id)).where(JobApplication.job_id == job.id))
    application_count = result.scalar()

    return JobOfferOut(
        id=job.id,
        title=job.title,
        description=job.description,
        category=job.category,
        location=job.location,
        budget_min=job.budget_min,
        budget_max=job.budget_max,
        status=job.status,
        boost_until=job.boost_until,
        client_id=job.client_id,
        created_at=job.created_at,
        application_count=application_count,
    )


@router.get("", response_model=List[JobOfferOut])
async def search_jobs(
    category: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Public search - no verification needed"""
    query = select(JobOffer).where(JobOffer.status == JobStatus.open)

    if category:
        query = query.where(JobOffer.category.ilike(f"%{category}%"))
    if location:
        query = query.where(JobOffer.location.ilike(f"%{location}%"))

    # Premium/boost ranking
    query = query.order_by(
        # Boosted jobs first
        (JobOffer.boost_until > func.now()).desc(),
        # Newest first
        JobOffer.created_at.desc(),
    )

    result = await db.execute(query.limit(50))
    jobs = result.scalars().all()

    # Add application counts
    job_ids = [job.id for job in jobs]
    if job_ids:
        count_query = select(JobApplication.job_id, func.count(JobApplication.id)).where(
            JobApplication.job_id.in_(job_ids)
        ).group_by(JobApplication.job_id)
        counts = await db.execute(count_query)
        count_dict = dict(counts.all())

    return [
        JobOfferOut(
            id=job.id,
            title=job.title,
            description=job.description,
            category=job.category,
            location=job.location,
            budget_min=job.budget_min,
            budget_max=job.budget_max,
            status=job.status,
            boost_until=job.boost_until,
            client_id=job.client_id,
            created_at=job.created_at,
            application_count=count_dict.get(job.id, 0),
        )
        for job in jobs
    ]


@router.post("/{job_id}/apply", response_model=JobApplicationOut, status_code=status.HTTP_201_CREATED)
async def apply_to_job(
    job_id: int,
    data: JobApplicationCreate,
    current_worker: User = Depends(get_verified_worker),
    db: AsyncSession = Depends(get_db),
):
    """Apply to job - VERIFIED WORKERS ONLY"""
    # Check job exists and is open
    job = await db.get(JobOffer, job_id)
    if not job or job.status != JobStatus.open:
        raise HTTPException(status_code=404, detail="Job not found or closed")

    # Prevent duplicate applications
    result = await db.execute(
        select(JobApplication)
        .where(JobApplication.job_id == job_id, JobApplication.worker_id == current_worker.id)
    )
    if result.scalar():
        raise HTTPException(status_code=400, detail="Already applied")

    application = JobApplication(
        job_id=job_id,
        worker_id=current_worker.id,
        cover_message=data.cover_message,
    )
    db.add(application)
    await db.commit()
    await db.refresh(application)

    return JobApplicationOut(
        id=application.id,
        job_id=application.job_id,
        worker_id=application.worker_id,
        cover_message=application.cover_message,
        status=application.status,
        created_at=application.created_at,
    )


@router.get("/{job_id}/applications", response_model=List[JobApplicationOut])
async def list_job_applications(
    job_id: int,
    current_client: User = Depends(get_verified_client),
    db: AsyncSession = Depends(get_db),
):
    """List applications for a job - VERIFIED CLIENT OWNERS ONLY"""
    job = await db.get(JobOffer, job_id)
    if not job or job.client_id != current_client.id:
        raise HTTPException(status_code=403, detail="Not your job")

    result = await db.execute(
        select(JobApplication)
        .where(JobApplication.job_id == job_id)
        .order_by(JobApplication.created_at.desc())
    )
    applications = result.scalars().all()

    return [
        JobApplicationOut(
            id=app.id,
            job_id=app.job_id,
            worker_id=app.worker_id,
            cover_message=app.cover_message,
            status=app.status,
            created_at=app.created_at,
        )
        for app in applications
    ]



@router.post("/{job_id}/applications/{application_id}/accept")
async def accept_application(
    job_id: int,
    application_id: int,
    current_client: User = Depends(get_verified_client),
    db: AsyncSession = Depends(get_db),
):
    # Only the owner client of this job can accept
    job = await db.get(JobOffer, job_id)
    if not job or job.client_id != current_client.id:
        raise HTTPException(status_code=403, detail="Not your job")

    application = await db.get(JobApplication, application_id)
    if not application or application.job_id != job_id:
        raise HTTPException(status_code=404, detail="Application not found")

    if application.status != JobApplicationStatus.pending:
        raise HTTPException(status_code=400, detail="Already processed")

    application.status = JobApplicationStatus.accepted
    await db.commit()
    await db.refresh(application)

    return {"message": "Application accepted", "status": application.status}


@router.post("/{job_id}/applications/{application_id}/reject")
async def reject_application(
    job_id: int,
    application_id: int,
    current_client: User = Depends(get_verified_client),
    db: AsyncSession = Depends(get_db),
):
    # Only the owner client of this job can reject
    job = await db.get(JobOffer, job_id)
    if not job or job.client_id != current_client.id:
        raise HTTPException(status_code=403, detail="Not your job")

    application = await db.get(JobApplication, application_id)
    if not application or application.job_id != job_id:
        raise HTTPException(status_code=404, detail="Application not found")

    if application.status != JobApplicationStatus.pending:
        raise HTTPException(status_code=400, detail="Already processed")

    application.status = JobApplicationStatus.rejected
    await db.commit()
    await db.refresh(application)

    return {"message": "Application rejected", "status": application.status}
