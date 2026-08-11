from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import (
    String,
    Integer,
    Enum,
    DECIMAL,
    ForeignKey,
    JSON,
    DateTime,
    func,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class UserRole(str, PyEnum):
    worker = "worker"
    client = "client"
    admin = "admin"

class VerificationStatus(str, PyEnum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"),
        nullable=False,
    )

    created_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    worker_profile: Mapped[Optional["WorkerProfile"]] = relationship(
        back_populates="user", uselist=False
    )
    client_profile: Mapped[Optional["ClientProfile"]] = relationship(
        back_populates="user", uselist=False
    )
    job_offers: Mapped[List["JobOffer"]] = relationship("JobOffer")
    services: Mapped[List["Service"]] = relationship("Service", back_populates="provider")


class WorkerProfile(Base):
    __tablename__ = "worker_profiles"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), primary_key=True
    )

    bio: Mapped[Optional[str]] = mapped_column(nullable=True)
    categories: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    hourly_rate: Mapped[Optional[float]] = mapped_column(
        DECIMAL(10, 2), nullable=True
    )
    location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    availability: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    portfolio_urls: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    verified: Mapped[bool] = mapped_column(default=False)

    # NEW:
    status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, name="verification_status"),
        default=VerificationStatus.pending,
        nullable=False,
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    premium_until: Mapped[Optional["DateTime"]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rating: Mapped[Optional[float]] = mapped_column(DECIMAL(3, 2), nullable=True)

    user: Mapped["User"] = relationship(back_populates="worker_profile")


class ClientProfile(Base):
    __tablename__ = "client_profiles"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), primary_key=True
    )

    company_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verified: Mapped[bool] = mapped_column(default=False)

    # IMPORTANT: reuse the same Postgres enum name as worker_profiles
    status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, name="verification_status"),
        default=VerificationStatus.pending,
        nullable=False,
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="client_profile")
