"""
Shared pytest fixtures. Tests run against an in-memory SQLite database
(via a dependency override on get_db) so they never touch the real MySQL
database and need no external services — GROQ_API_KEY is left unset so
ai.py falls back to its mock generator instead of making network calls.
"""

import asyncio
import os
import sys

if sys.platform == "win32":
    # aiosqlite deadlocks on connection teardown under Windows' default
    # ProactorEventLoop (a known interaction between its IOCP-based
    # implementation and aiosqlite's background-thread worker) — this only
    # affects the SQLite test database; production uses MySQL/aiomysql and
    # a single long-lived event loop, so it never hits this path.
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Must be set before `app.config` is imported (below) — python-dotenv's
# load_dotenv() does not override variables already present in os.environ,
# so this takes precedence over whatever is in backend/.env.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("ENVIRONMENT", "development")

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# StaticPool: every connection shares the same in-memory database. Without
# it, each new connection would get its own separate (empty) :memory: db.
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = async_sessionmaker(bind=test_engine, expire_on_commit=False)


async def _override_get_db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = _override_get_db


@pytest_asyncio.fixture(autouse=True)
async def _fresh_schema():
    """Recreate all tables before every test so tests don't leak state."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _dispose_engine():
    """Close the shared SQLite connection once the session ends.

    aiosqlite runs each connection in a non-daemon worker thread; with
    StaticPool that connection is never returned/closed, so without this the
    interpreter waits on the thread forever after the last test passes.
    """
    yield
    await test_engine.dispose()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient) -> str:
    """
    Admin accounts aren't self-serve (see create_admin.py) — insert one
    directly into the test database, the same way that script does.
    """
    from app.security import hash_password
    from app.user import User, UserRole

    async with TestSessionLocal() as session:
        admin = User(
            email="admin@test.tn",
            phone="20000000",
            password_hash=hash_password("AdminPass123!"),
            role=UserRole.admin,
        )
        session.add(admin)
        await session.commit()

    resp = await client.post("/auth/login", data={"username": "admin@test.tn", "password": "AdminPass123!"})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


async def register_and_login(client: AsyncClient, *, role: str, email: str, phone: str) -> str:
    """Helper: registers a user and returns a bearer access token."""
    resp = await client.post(
        "/auth/register/simple",
        json={"email": email, "password": "testpass123", "phone": phone, "role": role, "address": "Tunis"},
    )
    assert resp.status_code == 201, resp.text
    resp = await client.post("/auth/login", data={"username": email, "password": "testpass123"})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
