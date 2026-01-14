from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
# Copy EXACTLY from your auth.py imports ↓
from ..core.database import get_db
from ..models.user import User, UserRole
from ..models.worker_profile import WorkerProfile
from .dependencies import get_current_admin_user  # Your deps file

admin_router = APIRouter(prefix="/admin", tags=["Admin"])

@admin_router.get("/workers/unverified")
async def get_unverified_workers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    result = await db.execute(
        select(User, WorkerProfile)
        .join(WorkerProfile)
        .where(WorkerProfile.verified == False)
    )
    workers = result.all()
    return [{"user_id": u.id, "email": u.email} for u, wp in workers]

@admin_router.patch("/workers/{user_id}/verify")
async def verify_worker(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    user = await db.get(User, user_id)
    if not user or user.role != UserRole.worker:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid worker")
    
    user.is_verified = True
    
    wp = await db.execute(select(WorkerProfile).where(WorkerProfile.user_id == user_id))
    worker_profile = wp.scalar_one_or_none()
    if worker_profile:
        worker_profile.verified = True
    
    await db.commit()
    return {"message": f"Worker {user_id} verified ✅"}
