import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.subscriptions import SubscriptionPlan
from sqlalchemy import select
# Import models
from app.user import User
from app.jobs import JobOffer
from app.service import Service
from app.bookings import Booking
from app.reviews import Review
from app.wallet import Wallet
from app.chat import Message

async def seed_plans():
    plans_data = [
        {
            "name": "Starter", 
            "description": "Basic visibility for new workers",
            "price": 15.00, 
            "duration_days": 30, 
            "features": {"visibility": "standard", "max_bids": 10}
        },
        {
            "name": "Professional", 
            "description": "Enhanced visibility and pro badge",
            "price": 40.00, 
            "duration_days": 30, 
            "features": {"visibility": "high", "badge": "pro", "max_bids": 50}
        },
        {
            "name": "Business", 
            "description": "Maximum reach and priority support",
            "price": 100.00, 
            "duration_days": 30, 
            "features": {"visibility": "max", "badge": "business", "priority_support": True, "max_bids": -1}
        }
    ]

    async with AsyncSessionLocal() as db:
        for plan_data in plans_data:
            # Check if exists
            result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.name == plan_data["name"]))
            existing = result.scalar_one_or_none()
            
            if existing:
                print(f"Plan {plan_data['name']} already exists. Updating price...")
                existing.price = plan_data["price"]
                existing.description = plan_data["description"]
                existing.features = plan_data["features"]
            else:
                print(f"Creating plan {plan_data['name']}...")
                plan = SubscriptionPlan(**plan_data)
                db.add(plan)
        
        await db.commit()
        print("Seeding completed.")

if __name__ == "__main__":
    try:
        asyncio.run(seed_plans())
    except Exception as e:
        print(f"Error seeding plans: {e}")
