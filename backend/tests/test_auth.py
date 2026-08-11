from httpx import AsyncClient

from conftest import auth_header, register_and_login


async def test_register_and_login(client: AsyncClient):
    token = await register_and_login(client, role="worker", email="w1@test.tn", phone="20000001")
    resp = await client.get("/auth/me", headers=auth_header(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "w1@test.tn"
    assert body["role"] == "worker"


async def test_duplicate_email_rejected(client: AsyncClient):
    await register_and_login(client, role="worker", email="dupe@test.tn", phone="20000002")
    resp = await client.post(
        "/auth/register/simple",
        json={"email": "dupe@test.tn", "password": "testpass123", "phone": "20000003", "role": "worker"},
    )
    assert resp.status_code == 400


async def test_cannot_self_register_as_admin(client: AsyncClient):
    resp = await client.post(
        "/auth/register/simple",
        json={"email": "wannabe@test.tn", "password": "testpass123", "phone": "20000004", "role": "admin"},
    )
    assert resp.status_code == 422  # rejected by the pydantic schema validator


async def test_short_password_rejected(client: AsyncClient):
    resp = await client.post(
        "/auth/register/simple",
        json={"email": "short@test.tn", "password": "abc", "phone": "20000005", "role": "worker"},
    )
    assert resp.status_code == 422


async def test_invalid_phone_rejected(client: AsyncClient):
    resp = await client.post(
        "/auth/register/simple",
        json={"email": "badphone@test.tn", "password": "testpass123", "phone": "123", "role": "worker"},
    )
    assert resp.status_code == 422


async def test_wallet_auto_created_on_register(client: AsyncClient):
    token = await register_and_login(client, role="client", email="c1@test.tn", phone="20000006")
    resp = await client.get("/wallet/me", headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.json()["balance"] == 0.0


async def test_wrong_password_rejected(client: AsyncClient):
    await register_and_login(client, role="worker", email="w2@test.tn", phone="20000007")
    resp = await client.post("/auth/login", data={"username": "w2@test.tn", "password": "wrongpassword"})
    assert resp.status_code == 401


async def test_unauthenticated_request_rejected(client: AsyncClient):
    resp = await client.get("/auth/me")
    assert resp.status_code == 401
