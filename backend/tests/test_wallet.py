from httpx import AsyncClient

from conftest import auth_header, register_and_login


async def test_topup_requires_admin_approval(client: AsyncClient, admin_token: str):
    token = await register_and_login(client, role="worker", email="topup@test.tn", phone="20300001")

    resp = await client.post("/wallet/top-up", json={"amount": 100, "method": "manual"}, headers=auth_header(token))
    assert resp.status_code == 200
    tx = resp.json()
    assert tx["status"] == "pending"

    # Balance not yet credited
    resp = await client.get("/wallet/me", headers=auth_header(token))
    assert resp.json()["balance"] == 0.0

    resp = await client.post(f"/wallet/admin/transactions/{tx['id']}/approve", headers=auth_header(admin_token))
    assert resp.status_code == 200
    assert resp.json()["new_balance"] == 100.0

    resp = await client.get("/wallet/me", headers=auth_header(token))
    assert resp.json()["balance"] == 100.0


async def test_negative_topup_rejected(client: AsyncClient):
    token = await register_and_login(client, role="worker", email="negtopup@test.tn", phone="20300002")
    resp = await client.post("/wallet/top-up", json={"amount": -10, "method": "manual"}, headers=auth_header(token))
    assert resp.status_code == 400


async def test_non_admin_cannot_approve_transactions(client: AsyncClient):
    token = await register_and_login(client, role="worker", email="sneaky@test.tn", phone="20300003")
    resp = await client.post("/wallet/top-up", json={"amount": 50, "method": "manual"}, headers=auth_header(token))
    tx = resp.json()

    resp = await client.post(f"/wallet/admin/transactions/{tx['id']}/approve", headers=auth_header(token))
    assert resp.status_code == 403
