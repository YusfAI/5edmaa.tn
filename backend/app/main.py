from fastapi import FastAPI, Depends
from sqlalchemy import text
from .database import engine, AsyncSessionLocal
from .auth import router as auth_router, get_current_admin
from .user import User, WorkerProfile
from .admin import router as admin_router
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from .jobs import router as jobs_router
from .service import router as services_router
from .bookings import router as bookings_router



app = FastAPI(
    title="5edma.tn API",
    version="0.1.0",
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(admin_router)
app.include_router(jobs_router)
app.include_router(services_router)
app.include_router(bookings_router) 

@app.get("/health")
async def health_check():
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.get("/admin/me")
async def read_admin_me(current_admin: User = Depends(get_current_admin)):
    return {
        "id": current_admin.id,
        "email": current_admin.email,
        "role": current_admin.role.value,
    }

@app.get("/admin/workers/pending")
async def list_pending_workers(current_admin: User = Depends(get_current_admin)):
    from .database import get_db  # import here to avoid circular

    async def _list(db: AsyncSession):
        from sqlalchemy import select

        result = await db.execute(
            select(WorkerProfile).where(WorkerProfile.verified == False)  # noqa: E712
        )
        workers = result.scalars().all()
        return [
            {
                "user_id": w.user_id,
                "location": w.location,
                "verified": w.verified,
            }
            for w in workers
        ]

    # manually open a session because we're outside normal Depends stack
    async with AsyncSessionLocal() as db:
        return await _list(db)


@app.post("/admin/workers/{user_id}/verify")
async def verify_worker(
    user_id: int,
    current_admin: User = Depends(get_current_admin),
):
    async with AsyncSessionLocal() as db:  # type: AsyncSession
        # 1) Check worker profile exists
        result = await db.execute(
            select(WorkerProfile).where(WorkerProfile.user_id == user_id)
        )
        worker_profile = result.scalar_one_or_none()

        if not worker_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker profile not found",
            )

        if worker_profile.verified:
            return {"message": "Worker already verified"}

        # 2) Mark as verified
        worker_profile.verified = True
        await db.commit()
        await db.refresh(worker_profile)

        return {
            "message": "Worker verified successfully",
            "user_id": user_id,
            "worker_verified": True,
        }


@app.post("/admin/workers/{user_id}/reject")
async def reject_worker(
    user_id: int,
    rejection_reason: str = "Not specified",
    current_admin: User = Depends(get_current_admin),
):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(WorkerProfile).filter(WorkerProfile.user_id == user_id)
        )
        worker_profile = result.scalar_one_or_none()
        
        if not worker_profile:
            raise HTTPException(status_code=404, detail="Worker not found")
            
        worker_profile.verified = False
        # worker_profile.rejection_reason = rejection_reason  # uncomment if column exists
        await db.commit()
        
        return {"message": "Worker rejected", "user_id": user_id, "reason": rejection_reason}
