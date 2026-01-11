from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import AsyncSessionLocal  # adjust to your async session
from app.models.user import User
from app.models.worker_profile import WorkerProfile
from app.api.deps import get_current_admin

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/workers/{user_id}/verify")
async def verify_worker(  # ← async def
    user_id: int,
    current_admin: User = Depends(get_current_admin),
):
    async with AsyncSessionLocal() as db:  # ← async with
        # 1) Check user exists and is worker
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if user.role != "worker":
            raise HTTPException(status_code=400, detail="User is not a worker")

        # 2) Check worker profile
        result = await db.execute(
            select(WorkerProfile).filter(WorkerProfile.user_id == user_id)
        )
        worker_profile = result.scalar_one_or_none()

        if not worker_profile:
            raise HTTPException(status_code=404, detail="Worker profile not found")

        if worker_profile.verified:
            return {"message": "Worker already verified"}

        # 3) Mark verified
        worker_profile.verified = True
        await db.commit()
        await db.refresh(worker_profile)

        return {
            "message": "Worker verified successfully",
            "user_id": user.id,
            "worker_verified": worker_profile.verified,
        }
