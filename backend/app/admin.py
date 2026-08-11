from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from .database import AsyncSession, get_db
from .auth import get_current_admin
from .user import User, WorkerProfile, ClientProfile, UserRole, VerificationStatus

router = APIRouter(prefix="/admin", tags=["admin"])



class PendingClient(BaseModel):
    user_id: int
    email: str
    phone: str
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    location: Optional[str] = None
    verified: bool = False
    status: VerificationStatus
    rejection_reason: Optional[str] = None

class RejectRequest(BaseModel):
    rejection_reason: str



class PendingWorker(BaseModel):
    user_id: int
    email: str
    phone: str
    bio: Optional[str] = None
    location: Optional[str] = None
    categories: Optional[List[str]] = None
    verified: bool = False
    status: VerificationStatus
    rejection_reason: Optional[str] = None

PendingWorker.model_rebuild()
PendingClient.model_rebuild()


@router.get("/workers/pending", response_model=List[PendingWorker])
async def get_pending_workers(
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
   # workers
    result = await db.execute(
        select(User, WorkerProfile)
        .outerjoin(WorkerProfile, WorkerProfile.user_id == User.id)
        .where(
            and_(
                User.role == UserRole.worker,
                WorkerProfile.status == VerificationStatus.pending,
        )
    )
)

    pending = []
    for user, profile in result.all():
        pending.append(
            PendingWorker(
                user_id=user.id,
                email=user.email,
                phone=user.phone,
                bio=profile.bio,
                location=profile.location,
                categories=profile.categories,
                verified=profile.verified,
                status=profile.status,
                rejection_reason=profile.rejection_reason,
        )
    )
    return pending


@router.post("/workers/{user_id}/verify")
async def verify_worker(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    result = await db.execute(
        select(WorkerProfile).where(WorkerProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Worker not found")
    if profile.verified:
        raise HTTPException(status_code=400, detail="Worker already verified")

    profile.verified = True
    profile.status = VerificationStatus.approved
    profile.rejection_reason = None
    await db.commit()
    await db.refresh(profile)
    return {"message": f"Worker {user_id} verified", "verified": True}





@router.post("/workers/{user_id}/reject")
async def reject_worker(
    user_id: int,
    payload: RejectRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    result = await db.execute(
        select(WorkerProfile).where(WorkerProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Worker not found")

    profile.verified = False
    profile.status = VerificationStatus.rejected
    profile.rejection_reason = payload.rejection_reason

    await db.commit()
    await db.refresh(profile)
    return {"message": f"Worker {user_id} rejected", "verified": False, "status": profile.status}


@router.get("/clients/pending", response_model=List[PendingClient])
async def get_pending_clients(
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    # clients
    result = await db.execute(
        select(User, ClientProfile)
        .outerjoin(ClientProfile, ClientProfile.user_id == User.id)
        .where(
            and_(
                User.role == UserRole.client,
                ClientProfile.status == VerificationStatus.pending,
        )
    )
)

    pending = []
    for user, profile in result.all():
        pending.append(
            PendingClient(
                user_id=user.id,
                email=user.email,
                phone=user.phone,
                full_name=getattr(profile, "full_name", None),
                company_name=profile.company_name,
                location=profile.location,
                verified=profile.verified,
                status=profile.status,
                rejection_reason=profile.rejection_reason,
        )
    )
    return pending


@router.post("/clients/{user_id}/verify")
async def verify_client(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    result = await db.execute(
        select(ClientProfile).where(ClientProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail="Client not found")

    if profile.verified:
        raise HTTPException(status_code=400, detail="Client already verified")

    profile.verified = True
    profile.status = VerificationStatus.approved
    profile.rejection_reason = None

    await db.commit()
    await db.refresh(profile)
    return {"message": f"Client {user_id} verified", "verified": True}


@router.post("/clients/{user_id}/reject")
async def reject_client(
    user_id: int,
    payload: RejectRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    result = await db.execute(
        select(ClientProfile).where(ClientProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Client not found")

    profile.verified = False
    profile.status = VerificationStatus.rejected
    profile.rejection_reason = payload.rejection_reason

    await db.commit()
    await db.refresh(profile)
    return {"message": f"Client {user_id} rejected", "verified": False, "status": profile.status}


