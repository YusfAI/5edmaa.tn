# fix_user_role_type.py
import asyncio
from sqlalchemy import text

from app.database import engine


async def main():
    async with engine.begin() as conn:
        # 1) Create enum type if it doesn't exist
        await conn.execute(text("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_type WHERE typname = 'user_role'
            ) THEN
                CREATE TYPE user_role AS ENUM ('worker', 'client', 'admin');
            END IF;
        END$$;
        """))

        # 2) Ensure users.role uses this enum type
        await conn.execute(text("""
        ALTER TABLE users
        ALTER COLUMN role
        TYPE user_role
        USING role::user_role;
        """))

    print("Done: user_role enum and users.role fixed.")


if __name__ == "__main__":
    asyncio.run(main())
