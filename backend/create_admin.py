import asyncio
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.user import User, UserRole
from app.security import hash_password


async def main():
    async with AsyncSessionLocal() as db:
        # Check if admin already exists
        result = await db.execute(
            select(User).where(User.email == "admin@5edma.tn")
        )
        existing = result.scalar_one_or_none()
        if existing:
            print(f"Admin already exists with id={existing.id}")
            return

        admin = User(
            email="admin@5edma.tn",
            phone="+21600000000",
            password_hash=hash_password("AdminStrong123!"),
            role=UserRole.admin,
        )

        db.add(admin)
        await db.commit()
        await db.refresh(admin)
        print(f"Admin created with id={admin.id}")


if __name__ == "__main__":
    asyncio.run(main())
