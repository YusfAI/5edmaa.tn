from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import (
    select,
    String,
    Integer,
    ForeignKey,
    DECIMAL,
    DateTime,
    func,
    Enum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncSession

from .database import Base, get_db
from .user import User
from .auth import get_verified_client, get_verified_worker, get_current_user, get_current_admin


router = APIRouter(prefix="/wallet", tags=["wallet"])


# === MODELS ===

class TransactionType(str, PyEnum):
    topup = "topup"             # User adds money
    payment = "payment"         # Client pays for job (escrow)
    withdrawal = "withdrawal"   # Worker withdraws
    refund = "refund"           # Admin refunds client
    fee = "fee"                 # Platform fee (optional)
    release = "release"         # Escrow release to worker


class TransactionStatus(str, PyEnum):
    pending = "pending"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class Wallet(Base):
    __tablename__ = "wallets"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    balance: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0.00, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="TND")
    
    updated_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship()


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    
    type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, name="transaction_type"), nullable=False
    )
    amount: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus, name="transaction_status"), 
        default=TransactionStatus.pending
    )
    
    reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # e.g. "manual_topup", "job_123"
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    created_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship()


# === SCHEMAS ===

class WalletOut(BaseModel):
    user_id: int
    balance: float
    currency: str
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class TransactionOut(BaseModel):
    id: int
    user_id: int
    type: TransactionType
    amount: float
    status: TransactionStatus
    reference: Optional[str]
    description: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TopUpRequest(BaseModel):
    amount: float
    method: str = "manual"  # D17, Flouci, etc.


# === ENDPOINTS ===

@router.get("/me", response_model=WalletOut)
async def get_my_wallet(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current user's wallet.
    Automatically creates a wallet if one does not exist for the user.
    """
    wallet = await db.get(Wallet, current_user.id)
    if not wallet:
        # Auto-create wallet for new users
        wallet = Wallet(user_id=current_user.id, balance=0.00)
        db.add(wallet)
        await db.commit()
        await db.refresh(wallet)
    return wallet


@router.post("/top-up", response_model=TransactionOut)
async def request_top_up(
    data: TopUpRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Request a top-up (e.g., via bank transfer or D17).
    This creates a 'pending' transaction that an Admin must approve.
    """
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    # Ensure wallet exists
    wallet = await db.get(Wallet, current_user.id)
    if not wallet:
        wallet = Wallet(user_id=current_user.id, balance=0.00)
        db.add(wallet)

    transaction = Transaction(
        user_id=current_user.id,
        type=TransactionType.topup,
        amount=data.amount,
        status=TransactionStatus.pending,
        reference=f"req_{int(datetime.now().timestamp())}",
        description=f"Top-up via {data.method}"
    )
    
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)
    return transaction


@router.get("/transactions", response_model=List[TransactionOut])
async def list_my_transactions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all transactions for the current user."""
    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == current_user.id)
        .order_by(Transaction.created_at.desc())
    )
    return result.scalars().all()


# --- ADMIN ENDPOINTS ---

@router.get("/admin/transactions/pending", response_model=List[TransactionOut])
async def list_pending_transactions(
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin: List all pending top-up requests."""
    result = await db.execute(
        select(Transaction)
        .where(Transaction.status == TransactionStatus.pending)
        .order_by(Transaction.created_at.asc())
    )
    return result.scalars().all()


@router.post("/admin/transactions/{transaction_id}/approve")
async def approve_transaction(
    transaction_id: int,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin: Approve a pending transaction (e.g. confirm money received).
    This updates the user's wallet balance.
    """
    transaction = await db.get(Transaction, transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    if transaction.status != TransactionStatus.pending:
        raise HTTPException(status_code=400, detail="Transaction already processed")

    # Update Wallet
    wallet = await db.get(Wallet, transaction.user_id)
    if not wallet:
        wallet = Wallet(user_id=transaction.user_id, balance=0.00)
        db.add(wallet)
    
    if transaction.type == TransactionType.topup:
        wallet.balance = float(wallet.balance) + float(transaction.amount)
    elif transaction.type == TransactionType.withdrawal:
        # Check sufficient funds if not checked at request time
        if wallet.balance < transaction.amount:
             raise HTTPException(status_code=400, detail="Insufficient funds for withdrawal")
        wallet.balance = float(wallet.balance) - float(transaction.amount)

    transaction.status = TransactionStatus.completed
    
    await db.commit()
    return {"message": "Transaction approved", "new_balance": wallet.balance}


@router.post("/admin/transactions/{transaction_id}/reject")
async def reject_transaction(
    transaction_id: int,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin: Reject a pending transaction."""
    transaction = await db.get(Transaction, transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    if transaction.status != TransactionStatus.pending:
        raise HTTPException(status_code=400, detail="Transaction already processed")

    transaction.status = TransactionStatus.cancelled
    await db.commit()
    return {"message": "Transaction rejected"}
