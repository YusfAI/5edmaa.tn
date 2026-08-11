from httpx import AsyncClient

from conftest import auth_header, register_and_login


async def test_verify_worker_actually_unlocks_worker_gated_endpoints(client: AsyncClient, admin_token: str):
    """
    Regression test: admin.verify_worker used to only set
    WorkerProfile.verified, never .status — but get_verified_worker (the
    dependency every worker-only endpoint relies on) checks .status, not
    .verified. So approving a worker silently did nothing. Caught via a
    live smoke test against a real database; this pins the fix.
    """
    worker_token = await register_and_login(client, role="worker", email="regtest@test.tn", phone="20100001")

    # Before verification: gated endpoints must reject
    resp = await client.get("/jobs/applications/mine", headers=auth_header(worker_token))
    assert resp.status_code == 403

    me = await client.get("/auth/me", headers=auth_header(worker_token))
    user_id = me.json()["id"]

    resp = await client.post(f"/admin/workers/{user_id}/verify", headers=auth_header(admin_token))
    assert resp.status_code == 200
    assert resp.json()["verified"] is True

    # After verification: same endpoint must now succeed
    resp = await client.get("/jobs/applications/mine", headers=auth_header(worker_token))
    assert resp.status_code == 200

    worker_me = await client.get("/auth/worker/me", headers=auth_header(worker_token))
    assert worker_me.json()["status"] == "approved"


async def test_verify_client_unlocks_job_posting(client: AsyncClient, admin_token: str):
    client_token = await register_and_login(client, role="client", email="cverify@test.tn", phone="20100002")

    resp = await client.post(
        "/jobs",
        json={"title": "Test job", "description": "A sufficiently long description", "category": "Test", "location": "Tunis"},
        headers=auth_header(client_token),
    )
    assert resp.status_code == 403

    me = await client.get("/auth/me", headers=auth_header(client_token))
    user_id = me.json()["id"]
    resp = await client.post(f"/admin/clients/{user_id}/verify", headers=auth_header(admin_token))
    assert resp.status_code == 200

    resp = await client.post(
        "/jobs",
        json={"title": "Test job", "description": "A sufficiently long description", "category": "Test", "location": "Tunis"},
        headers=auth_header(client_token),
    )
    assert resp.status_code == 201


async def test_reject_worker_with_reason(client: AsyncClient, admin_token: str):
    worker_token = await register_and_login(client, role="worker", email="rejectme@test.tn", phone="20100003")
    me = await client.get("/auth/me", headers=auth_header(worker_token))
    user_id = me.json()["id"]

    resp = await client.post(
        f"/admin/workers/{user_id}/reject",
        json={"rejection_reason": "Photo de la CIN illisible"},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200

    worker_me = await client.get("/auth/worker/me", headers=auth_header(worker_token))
    body = worker_me.json()
    assert body["status"] == "rejected"
    assert body["rejection_reason"] == "Photo de la CIN illisible"


async def test_non_admin_cannot_access_admin_endpoints(client: AsyncClient):
    worker_token = await register_and_login(client, role="worker", email="notadmin@test.tn", phone="20100004")
    resp = await client.get("/admin/workers/pending", headers=auth_header(worker_token))
    assert resp.status_code == 403
