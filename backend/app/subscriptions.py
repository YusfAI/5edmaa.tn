from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, String, Integer, ForeignKey, DateTime, func, DECIMAL, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncSession

from .database import Base, get_db
from .user import User, WorkerProfile
from .jobs import JobOffer
from .auth import get_current_user
from .wallet import Wallet, Transaction, TransactionType, TransactionStatus

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

# === MODELS ===

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False) # e.g. 30
    features: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("subscription_plans.id"), index=True)
    
    start_date: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
    end_date: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    user: Mapped["User"] = relationship()
    plan: Mapped["SubscriptionPlan"] = relationship()

class JobBoost(Base):
    __tablename__ = "job_boosts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("job_offers.id"), index=True)
    
    boost_type: Mapped[str] = mapped_column(String(50), nullable=False) # 'homepage', 'category_top'
    start_date: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
    end_date: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), nullable=False)
    
    price_paid: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    
    job: Mapped["JobOffer"] = relationship()


# === SCHEMAS ===

class PlanOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    duration_days: int
    features: Optional[dict]

    model_config = ConfigDict(from_attributes=True)

class BoostCreate(BaseModel):
    job_id: int
    duration_days: int = 7
    boost_type: str = "category_top"

# === ENDPOINTS ===

@router.get("/plans", response_model=List[PlanOut])
async def list_plans(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.is_active == True))
    return result.scalars().all()

@router.post("/purchase/{plan_id}")
async def purchase_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Get Plan
    plan = await db.get(SubscriptionPlan, plan_id)
    if not plan or not plan.is_active:
         raise HTTPException(status_code=404, detail="Plan not found")

    # 2. Check Wallet Balance
    wallet = await db.get(Wallet, current_user.id)
    if not wallet or wallet.balance < plan.price:
        raise HTTPException(status_code=400, detail="Insufficient funds in wallet")

    # 3. Deduct from Wallet
    wallet.balance -= plan.price
    
    # 4. Create Transaction Record
    tx = Transaction(
        user_id=current_user.id,
        type=TransactionType.payment, 
        amount=plan.price, # Stored as positive amount, context is payment
        status=TransactionStatus.completed,
        description=f"Purchase subscription: {plan.name}",
        reference=f"sub_{plan.id}_{int(datetime.now().timestamp())}"
    )
    db.add(tx)

    # 5. Create Subscription
    end_date = datetime.now() + timedelta(days=plan.duration_days)
    
    # Deactivate existing sub?
    # Logic: Extend if exists? Or replace? 
    # MVP: Replace.
    
    sub = UserSubscription(
        user_id=current_user.id,
        plan_id=plan.id,
        end_date=end_date,
        is_active=True
    )
    db.add(sub)
    
    # Update profile premium status if applicable
    # We update worker_profile.premium_until
    if current_user.role == "worker":
        # Load profile
        q = select(WorkerProfile).where(WorkerProfile.user_id == current_user.id)
        res = await db.execute(q)
        profile = res.scalar_one_or_none()
        if profile:
            profile.premium_until = end_date

    await db.commit()
    return {"message": "Subscription purchased successfully", "end_date": end_date}


@router.post("/boost-job")
async def boost_job(
    data: BoostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Fixed price for boost for now, e.g. 20 TND per week
    PRICE_PER_DAY = 5.0
    price = float(PRICE_PER_DAY * data.duration_days)

    # 1. Get Job
    job = await db.get(JobOffer, data.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.client_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your job")

    # 2. Check Wallet
    wallet = await db.get(Wallet, current_user.id)
    if not wallet or wallet.balance < price:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    # 3. Deduct
    wallet.balance -= price
    
    tx = Transaction(
        user_id=current_user.id,
        type=TransactionType.payment,
        amount=price,
        status=TransactionStatus.completed,
        description=f"Boost Job {job.title}",
        reference=f"boost_{job.id}_{int(datetime.now().timestamp())}"
    )
    db.add(tx)

    # 4. Create Boost Record
    end_date = datetime.now() + timedelta(days=data.duration_days)
    boost = JobBoost(
        job_id=job.id,
        boost_type=data.boost_type,
        end_date=end_date,
        price_paid=price
    )
    db.add(boost)

    # Extend (or set) the job's boost window — this is what search ranking in
    # jobs.py's search_jobs() actually orders on.
    job.boost_until = max(end_date, job.boost_until or end_date)

    await db.commit()
    return {"message": "Job boosted successfully", "end_date": end_date}
