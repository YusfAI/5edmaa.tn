from datetime import datetime
from typing import List, Optional

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
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel

from .database import Base, get_db
from .auth import get_verified_worker
from .user import User

router = APIRouter(prefix="/services", tags=["services"])


# === MODELS ===

class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    category: Mapped[str] = mapped_column(String(100), index=True)
    location: Mapped[str] = mapped_column(String(100), index=True)

    base_price: Mapped[Optional[float]] = mapped_column(
        DECIMAL(10, 2), nullable=True
    )
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    provider: Mapped["User"] = relationship(back_populates="services")



# === Pydantic Schemas ===

class ServiceCreate(BaseModel):
    title: str
    description: str
    category: str
    location: str
    base_price: Optional[float] = None
    is_premium: bool = False


class ServiceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    base_price: Optional[float] = None
    is_premium: Optional[bool] = None


class ServiceOut(BaseModel):
    id: int
    provider_id: int
    title: str
    description: str
    category: str
    location: str
    base_price: Optional[float]
    is_premium: bool
    created_at: datetime

    class Config:
        from_attributes = True

# === ENDPOINTS ===

@router.post("", response_model=ServiceOut, status_code=status.HTTP_201_CREATED)
async def create_service(
    data: ServiceCreate,
    current_worker: User = Depends(get_verified_worker),
    db: AsyncSession = Depends(get_db),
):
    """Create a service - VERIFIED WORKERS ONLY"""
    service = Service(
        provider_id=current_worker.id,
        **data.dict(),
    )
    db.add(service)
    await db.commit()
    await db.refresh(service)
    return service


@router.get("", response_model=List[ServiceOut])
async def list_services(
    category: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    provider_id: Optional[int] = Query(None),
    is_premium: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Public services catalog"""
    query = select(Service)

    if category:
        query = query.where(Service.category.ilike(f"%{category}%"))
    if location:
        query = query.where(Service.location.ilike(f"%{location}%"))
    if provider_id:
        query = query.where(Service.provider_id == provider_id)
    if is_premium is not None:
        query = query.where(Service.is_premium == is_premium)

    query = query.order_by(
        Service.is_premium.desc(),  # premium first
        Service.created_at.desc(),  # newest first
    )

    result = await db.execute(query.limit(50))
    return result.scalars().all()


@router.patch("/{service_id}", response_model=ServiceOut)
async def update_service(
    service_id: int,
    data: ServiceUpdate,
    current_worker: User = Depends(get_verified_worker),
    db: AsyncSession = Depends(get_db),
):
    """Update own service - VERIFIED WORKERS ONLY"""
    service = await db.get(Service, service_id)
    if not service or service.provider_id != current_worker.id:
        raise HTTPException(status_code=404, detail="Service not found")

    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(service, key, value)

    await db.commit()
    await db.refresh(service)
    return service


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(
    service_id: int,
    current_worker: User = Depends(get_verified_worker),
    db: AsyncSession = Depends(get_db),
):
    """Delete own service - VERIFIED WORKERS ONLY"""
    service = await db.get(Service, service_id)
    if not service or service.provider_id != current_worker.id:
        raise HTTPException(status_code=404, detail="Service not found")

    await db.delete(service)
    await db.commit()
    return None
