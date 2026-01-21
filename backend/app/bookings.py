from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional
from .service import Service
from .auth import get_verified_client, get_verified_worker
from .database import Base, get_db


from sqlalchemy import (
    String,
    Integer,
    ForeignKey,
    DateTime,
    func,
    Enum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel

from .database import Base, get_db
from .auth import get_verified_client, get_verified_worker
from .user import User
from .service import Service  # Service model you already have


router = APIRouter(prefix="/bookings", tags=["bookings"])


# === MODELS ===

class BookingStatus(str, PyEnum):
    pending = "pending"      # client requested, waiting for worker
    confirmed = "confirmed"  # worker accepted
    cancelled = "cancelled"  # cancelled by client or worker
    completed = "completed"  # (optional) marked done


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    scheduled_for: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus, name="booking_status"),
        default=BookingStatus.pending,
    )

    # Optional note from client (address, details, etc.)
    note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    service: Mapped["Service"] = relationship()
    customer: Mapped["User"] = relationship(
        foreign_keys=[customer_id],
    )
    provider: Mapped["User"] = relationship(
        foreign_keys=[provider_id],
    )


# === Pydantic Schemas ===

class BookingCreate(BaseModel):
    service_id: int
    scheduled_for: datetime
    note: Optional[str] = None


class BookingOut(BaseModel):
    id: int
    service_id: int
    customer_id: int
    provider_id: int
    scheduled_for: datetime
    status: BookingStatus
    note: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# === ENDPOINTS ===

@router.post("", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
async def create_booking(
    data: BookingCreate,
    current_client: User = Depends(get_verified_client),
    db: AsyncSession = Depends(get_db),
):
    """Client creates a booking request for a service."""
    # 1) Check service exists
    service = await db.get(Service, data.service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    # 2) Create booking (pending)
    booking = Booking(
        service_id=service.id,
        customer_id=current_client.id,
        provider_id=service.provider_id,
        scheduled_for=data.scheduled_for,
        note=data.note,
    )

    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking


@router.get("/my", response_model=List[BookingOut])
async def list_my_bookings_client(
    current_client: User = Depends(get_verified_client),
    db: AsyncSession = Depends(get_db),
):
    """Client sees all their bookings."""
    from sqlalchemy import select

    result = await db.execute(
        select(Booking)
        .where(Booking.customer_id == current_client.id)
        .order_by(Booking.created_at.desc())
    )
    return result.scalars().all()


@router.get("/my-requests", response_model=List[BookingOut])
async def list_my_bookings_worker(
    current_worker: User = Depends(get_verified_worker),
    db: AsyncSession = Depends(get_db),
):
    """Worker sees bookings requests for their services."""
    from sqlalchemy import select

    result = await db.execute(
        select(Booking)
        .where(Booking.provider_id == current_worker.id)
        .order_by(Booking.created_at.desc())
    )
    return result.scalars().all()


@router.post("/{booking_id}/confirm", response_model=BookingOut)
async def confirm_booking(
    booking_id: int,
    current_worker: User = Depends(get_verified_worker),
    db: AsyncSession = Depends(get_db),
):
    """Worker confirms a pending booking."""
    booking = await db.get(Booking, booking_id)
    if not booking or booking.provider_id != current_worker.id:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.status != BookingStatus.pending:
        raise HTTPException(status_code=400, detail="Booking already processed")

    booking.status = BookingStatus.confirmed
    await db.commit()
    await db.refresh(booking)
    return booking


@router.post("/{booking_id}/cancel", response_model=BookingOut)
async def cancel_booking(
    booking_id: int,
    current_user: User = Depends(get_verified_client),  # will check role below
    db: AsyncSession = Depends(get_db),
):
    """
    Client or worker cancels a booking.
    - Client can cancel their own bookings.
    - Worker can cancel bookings for their services.
    """
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Allow cancel if current user is customer or provider
    if current_user.id not in (booking.customer_id, booking.provider_id):
        raise HTTPException(status_code=403, detail="Not allowed to cancel this booking")

    if booking.status not in (BookingStatus.pending, BookingStatus.confirmed):
        raise HTTPException(status_code=400, detail="Cannot cancel this booking")

    booking.status = BookingStatus.cancelled
    await db.commit()
    await db.refresh(booking)
    return booking
