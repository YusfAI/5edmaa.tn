from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy import text, select , func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional , List
from .database import engine, AsyncSessionLocal 
from .auth import router as auth_router, get_current_admin, get_current_user
from .user import User, WorkerProfile, UserRole , ClientProfile , Service
from pydantic import BaseModel
from app.database import get_db
from app.auth import router as auth_router, get_current_admin, get_current_user
from app import auth


app = FastAPI(
    title="5edma.tn API",
    version="0.1.0",
)


app.include_router(auth_router)




class ServiceCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    location: Optional[str] = None

    class Config:
        orm_mode = True



class ClientProfileUpdate(BaseModel):
    company_name: Optional[str] = None
    location: Optional[str] = None

    class Config:
        orm_mode = True



class WorkerProfileUpdate(BaseModel):
    bio: Optional[str] = None
    categories: Optional[List[str]] = None
    hourly_rate: Optional[float] = None
    location: Optional[str] = None
    availability: Optional[dict] = None
    portfolio_urls: Optional[List[str]] = None

    class Config:
        orm_mode = True




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


@app.get("/workers")
async def list_verified_workers(
    city: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = Query(default=20, le=100),
):
    async with AsyncSessionLocal() as db:  # type: AsyncSession
        # Base query: only verified workers
        stmt = select(WorkerProfile).where(WorkerProfile.verified == True)  # noqa: E712

        # Optional city filter (location contains city string)
        if city:
            stmt = stmt.where(WorkerProfile.location.ilike(f"%{city}%"))

        # Optional category filter (ARRAY of categories contains this category)
        if category:
            stmt = stmt.where(WorkerProfile.categories.any(category))

        # Total count for this filter (for pagination info)
        count_stmt = stmt.with_only_columns(func.count()).order_by(None)
        total_result = await db.execute(count_stmt)
        total = total_result.scalar_one()

        # Apply pagination
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        workers = result.scalars().all()

        return {
            "items": [
                {
                    "user_id": w.user_id,
                    "bio": w.bio,
                    "categories": w.categories,
                    "hourly_rate": float(w.hourly_rate) if w.hourly_rate is not None else None,
                    "location": w.location,
                    "rating": float(w.rating) if w.rating is not None else None,
                    "verified": w.verified,
                }
                for w in workers
            ],
            "total": total,
            "skip": skip,
            "limit": limit,
            "filters": {
                "city": city,
                "category": category,
            },
        }


@app.get("/workers/me")
async def get_my_worker_profile(
    current_user: User = Depends(get_current_user),
):
    # Ensure the logged-in user is a worker
    if current_user.role != UserRole.worker:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workers can access their worker profile",
        )

    async with AsyncSessionLocal() as db:  # type: AsyncSession
        result = await db.execute(
            select(WorkerProfile).where(WorkerProfile.user_id == current_user.id)
        )
        worker_profile = result.scalar_one_or_none()

        if worker_profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker profile not found",
            )

        return {
            "user_id": current_user.id,
            "email": current_user.email,
            "phone": current_user.phone,
            "location": worker_profile.location,
            "verified": worker_profile.verified,
        }


@app.put("/workers/me")
async def update_my_worker_profile(
    payload: WorkerProfileUpdate,
    current_user: User = Depends(get_current_user),
):
    # Only workers can update worker profile
    if current_user.role != UserRole.worker:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workers can update worker profile",
        )

    async with AsyncSessionLocal() as db:  # type: AsyncSession
        result = await db.execute(
            select(WorkerProfile).where(WorkerProfile.user_id == current_user.id)
        )
        worker_profile = result.scalar_one_or_none()

        if worker_profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker profile not found",
            )

        # Apply partial updates only for provided fields
        if payload.bio is not None:
            worker_profile.bio = payload.bio
        if payload.categories is not None:
            worker_profile.categories = payload.categories
        if payload.hourly_rate is not None:
            worker_profile.hourly_rate = payload.hourly_rate
        if payload.location is not None:
            worker_profile.location = payload.location
        if payload.availability is not None:
            worker_profile.availability = payload.availability
        if payload.portfolio_urls is not None:
            worker_profile.portfolio_urls = payload.portfolio_urls

        await db.commit()
        await db.refresh(worker_profile)

        return {
            "user_id": current_user.id,
            "email": current_user.email,
            "phone": current_user.phone,
            "bio": worker_profile.bio,
            "categories": worker_profile.categories,
            "hourly_rate": float(worker_profile.hourly_rate) if worker_profile.hourly_rate is not None else None,
            "location": worker_profile.location,
            "availability": worker_profile.availability,
            "portfolio_urls": worker_profile.portfolio_urls,
            "verified": worker_profile.verified,
        }


@app.patch("/auth/verify")
async def verify_worker(
    current_user: User = Depends(get_current_user),

    db: AsyncSession = Depends(get_db)
):
    current_user.is_verified = True
    await db.commit()
    await db.refresh(current_user)
    return {"message": "Worker verified"}



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



@app.get("/clients/me")
async def get_my_client_profile(
    current_user: User = Depends(get_current_user),
):
    # Only clients can access this
    if current_user.role != UserRole.client:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only clients can access their client profile",
        )

    async with AsyncSessionLocal() as db:  # type: AsyncSession
        result = await db.execute(
            select(ClientProfile).where(ClientProfile.user_id == current_user.id)
        )
        client_profile = result.scalar_one_or_none()

        if client_profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client profile not found",
            )

        return {
            "user_id": current_user.id,
            "email": current_user.email,
            "phone": current_user.phone,
            "company_name": client_profile.company_name,
            "location": client_profile.location,
        }

@app.put("/clients/me")
async def update_my_client_profile(
    payload: ClientProfileUpdate,
    current_user: User = Depends(get_current_user),
):
    # Only clients can update client profile
    if current_user.role != UserRole.client:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only clients can update client profile",
        )

    async with AsyncSessionLocal() as db:  # type: AsyncSession
        result = await db.execute(
            select(ClientProfile).where(ClientProfile.user_id == current_user.id)
        )
        client_profile = result.scalar_one_or_none()

        if client_profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client profile not found",
            )

        # Partial updates
        if payload.company_name is not None:
            client_profile.company_name = payload.company_name
        if payload.location is not None:
            client_profile.location = payload.location

        await db.commit()
        await db.refresh(client_profile)

        return {
            "user_id": current_user.id,
            "email": current_user.email,
            "phone": current_user.phone,
            "company_name": client_profile.company_name,
            "location": client_profile.location,
        }




@app.post("/services", status_code=status.HTTP_201_CREATED)
async def create_service(
    payload: ServiceCreate,
    current_user: User = Depends(get_current_user),
):
    # 1) Ensure current user is a worker
    if current_user.role != UserRole.worker:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workers can create services",
        )

    async with AsyncSessionLocal() as db:  # type: AsyncSession
        # 2) Ensure worker is verified
        result = await db.execute(
            select(WorkerProfile).where(WorkerProfile.user_id == current_user.id)
        )
        worker_profile = result.scalar_one_or_none()

        if worker_profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker profile not found",
            )

        if not worker_profile.verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only verified workers can create services",
            )

        # 3) Create service
        service = Service(
            worker_id=current_user.id,
            title=payload.title,
            description=payload.description,
            category=payload.category,
            price=payload.price,
            location=payload.location or worker_profile.location,
        )

        db.add(service)
        await db.commit()
        await db.refresh(service)

        return {
            "id": service.id,
            "worker_id": service.worker_id,
            "title": service.title,
            "description": service.description,
            "category": service.category,
            "price": float(service.price) if service.price is not None else None,
            "location": service.location,
            "is_active": service.is_active,
            "created_at": service.created_at,
        }
