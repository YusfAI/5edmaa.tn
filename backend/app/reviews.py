from datetime import datetime
from typing import List, Optional

from sqlalchemy import Integer, ForeignKey, Text, DateTime, func, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .jobs import JobOffer, JobApplication, JobApplicationStatus
from fastapi import APIRouter, Depends, HTTPException, status

from pydantic import BaseModel, ConfigDict, conint

from .database import Base, get_db
from .user import User, WorkerProfile
from .bookings import Booking, BookingStatus
from .auth import get_verified_client, get_verified_worker , get_current_user

router = APIRouter(prefix="/reviews", tags=["reviews"])


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # EXISTING
    booking_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("bookings.id"),
        index=True,
        nullable=True,  # <-- make nullable
    )

    # NEW: job-application based reviews
    job_application_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("job_applications.id"),
        index=True,
        nullable=True,
    )

    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    reviewee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 1–5
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    booking: Mapped[Optional["Booking"]] = relationship()
    job_application: Mapped[Optional["JobApplication"]] = relationship()
    reviewer: Mapped["User"] = relationship(foreign_keys=[reviewer_id])
    reviewee: Mapped["User"] = relationship(foreign_keys=[reviewee_id])

class ReviewCreate(BaseModel):
    rating: conint(ge=1, le=5)
    comment: Optional[str] = None


class ReviewOut(BaseModel):
    id: int
    booking_id: Optional[int] = None          # <-- make optional
    job_application_id: Optional[int] = None  # <-- add this
    reviewer_id: int
    reviewee_id: int
    rating: int
    comment: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)





async def _recalculate_worker_rating(
    worker_id: int,
    db: AsyncSession,
):
    # average rating where reviewee_id == worker_id
    result = await db.execute(
        select(func.avg(Review.rating)).where(Review.reviewee_id == worker_id)
    )
    avg_rating = result.scalar()

    worker_profile = await db.execute(
        select(WorkerProfile).where(WorkerProfile.user_id == worker_id)
    )
    worker_profile = worker_profile.scalar_one_or_none()

    if worker_profile:
        worker_profile.rating = avg_rating
        await db.commit()
        await db.refresh(worker_profile)



@router.post(
    "/bookings/{booking_id}/review-as-client",
    response_model=ReviewOut,
    status_code=status.HTTP_201_CREATED,
)
async def review_as_client(
    booking_id: int,
    data: ReviewCreate,
    current_client: User = Depends(get_verified_client),
    db: AsyncSession = Depends(get_db),
):
    # 1) Load booking and check ownership
    booking = await db.get(Booking, booking_id)
    if not booking or booking.customer_id != current_client.id:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.status != BookingStatus.completed:
        raise HTTPException(status_code=400, detail="Booking must be completed to review")

    # 2) Check client has not already reviewed this booking
    existing = await db.execute(
        select(Review).where(
            Review.booking_id == booking_id,
            Review.reviewer_id == current_client.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="You already reviewed this booking")

    # 3) Create review: client (reviewer) -> worker (reviewee)
    review = Review(
        booking_id=booking_id,
        reviewer_id=current_client.id,
        reviewee_id=booking.provider_id,
        rating=data.rating,
        comment=data.comment,
    )

    db.add(review)
    await db.commit()
    await db.refresh(review)

    # 4) Recalculate worker rating
    await _recalculate_worker_rating(booking.provider_id, db)

    return review


@router.post(
    "/bookings/{booking_id}/review-as-worker",
    response_model=ReviewOut,
    status_code=status.HTTP_201_CREATED,
)
async def review_as_worker(
    booking_id: int,
    data: ReviewCreate,
    current_worker: User = Depends(get_verified_worker),
    db: AsyncSession = Depends(get_db),
):
    booking = await db.get(Booking, booking_id)
    if not booking or booking.provider_id != current_worker.id:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.status != BookingStatus.completed:
        raise HTTPException(status_code=400, detail="Booking must be completed to review")

    existing = await db.execute(
        select(Review).where(
            Review.booking_id == booking_id,
            Review.reviewer_id == current_worker.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="You already reviewed this booking")

    review = Review(
        booking_id=booking_id,
        reviewer_id=current_worker.id,
        reviewee_id=booking.customer_id,
        rating=data.rating,
        comment=data.comment,
    )

    db.add(review)
    await db.commit()
    await db.refresh(review)

    # Optional: later you can also maintain ClientProfile.rating here

    return review
@router.get("/workers/{worker_id}", response_model=List[ReviewOut])
async def list_worker_reviews(
    worker_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Review)
        .where(Review.reviewee_id == worker_id)
        .order_by(Review.created_at.desc())
    )
    return result.scalars().all()




@router.post(
    "/jobs/{job_id}/applications/{application_id}/review-as-client",
    response_model=ReviewOut,
    status_code=status.HTTP_201_CREATED,
)
async def review_job_application_as_client(
    job_id: int,
    application_id: int,
    data: ReviewCreate,
    current_client: User = Depends(get_verified_client),
    db: AsyncSession = Depends(get_db),
):
    # 1) Load job and check ownership
    job = await db.get(JobOffer, job_id)
    if not job or job.client_id != current_client.id:
        raise HTTPException(status_code=403, detail="Not your job")

    # 2) Load application and check it belongs to this job and is accepted
    application = await db.get(JobApplication, application_id)
    if not application or application.job_id != job_id:
        raise HTTPException(status_code=404, detail="Application not found")

    if application.status != JobApplicationStatus.accepted:
        raise HTTPException(status_code=400, detail="Only accepted applications can be reviewed")

    # 3) Prevent duplicate review (client for this application)
    existing = await db.execute(
        select(Review).where(
            Review.job_application_id == application_id,
            Review.reviewer_id == current_client.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="You already reviewed this job application")

    # 4) Create review: client -> worker
    review = Review(
        booking_id=None,
        job_application_id=application_id,
        reviewer_id=current_client.id,
        reviewee_id=application.worker_id,
        rating=data.rating,
        comment=data.comment,
    )

    db.add(review)
    await db.commit()
    await db.refresh(review)

    # 5) Recalculate worker rating (same helper)
    await _recalculate_worker_rating(application.worker_id, db)

    return review

@router.post(
    "/jobs/{job_id}/applications/{application_id}/review-as-worker",
    response_model=ReviewOut,
    status_code=status.HTTP_201_CREATED,
)
async def review_job_application_as_worker(
    job_id: int,
    application_id: int,
    data: ReviewCreate,
    current_worker: User = Depends(get_verified_worker),
    db: AsyncSession = Depends(get_db),
):
    # 1) Load application and check it belongs to this worker and job
    application = await db.get(JobApplication, application_id)
    if not application or application.job_id != job_id:
        raise HTTPException(status_code=404, detail="Application not found")

    if application.worker_id != current_worker.id:
        raise HTTPException(status_code=403, detail="Not your application")

    if application.status != JobApplicationStatus.accepted:
        raise HTTPException(status_code=400, detail="Only accepted applications can be reviewed")

    # 2) Load job to know client_id
    job = await db.get(JobOffer, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # 3) Prevent duplicate review (worker for this application)
    existing = await db.execute(
        select(Review).where(
            Review.job_application_id == application_id,
            Review.reviewer_id == current_worker.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="You already reviewed this job application")

    # 4) Create review: worker -> client
    review = Review(
        booking_id=None,
        job_application_id=application_id,
        reviewer_id=current_worker.id,
        reviewee_id=job.client_id,
        rating=data.rating,
        comment=data.comment,
    )

    db.add(review)
    await db.commit()
    await db.refresh(review)

    # (Optional) later: recalc client rating if you add it

    return review



@router.get("/services/{service_id}", response_model=List[ReviewOut])
async def list_service_reviews(
    service_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    List all reviews for a given service, based on bookings of that service.
    """
    result = await db.execute(
        select(Review)
        .join(Booking, Review.booking_id == Booking.id)
        .where(Booking.service_id == service_id)
        .order_by(Review.created_at.desc())
    )
    return result.scalars().all()


@router.get("/me/received", response_model=List[ReviewOut])
async def list_my_received_reviews(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List reviews received by the current user (as worker or client).
    """
    result = await db.execute(
        select(Review)
        .where(Review.reviewee_id == current_user.id)
        .order_by(Review.created_at.desc())
    )
    return result.scalars().all()




@router.get("/me/given", response_model=List[ReviewOut])
async def list_my_given_reviews(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List reviews written by the current user (as client or worker).
    """
    result = await db.execute(
        select(Review)
        .where(Review.reviewer_id == current_user.id)
        .order_by(Review.created_at.desc())
    )
    return result.scalars().all()
