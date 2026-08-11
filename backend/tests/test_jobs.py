from httpx import AsyncClient

from conftest import auth_header, register_and_login


async def _verified_client(client: AsyncClient, admin_token: str, email: str, phone: str) -> str:
    token = await register_and_login(client, role="client", email=email, phone=phone)
    me = await client.get("/auth/me", headers=auth_header(token))
    await client.post(f"/admin/clients/{me.json()['id']}/verify", headers=auth_header(admin_token))
    return token


async def _verified_worker(client: AsyncClient, admin_token: str, email: str, phone: str) -> tuple[str, int]:
    token = await register_and_login(client, role="worker", email=email, phone=phone)
    me = await client.get("/auth/me", headers=auth_header(token))
    user_id = me.json()["id"]
    await client.post(f"/admin/workers/{user_id}/verify", headers=auth_header(admin_token))
    return token, user_id


async def test_full_job_lifecycle(client: AsyncClient, admin_token: str):
    client_token = await _verified_client(client, admin_token, "jobclient@test.tn", "20200001")
    worker_token, worker_id = await _verified_worker(client, admin_token, "jobworker@test.tn", "20200002")

    resp = await client.post(
        "/jobs",
        json={
            "title": "Réparer une fuite d'eau",
            "description": "Fuite sous l'évier, assez urgent",
            "category": "Plomberie",
            "location": "Tunis",
            "budget_min": 50,
            "budget_max": 100,
        },
        headers=auth_header(client_token),
    )
    assert resp.status_code == 201
    job = resp.json()
    assert job["application_count"] == 0

    # Appears in public search
    resp = await client.get("/jobs")
    assert resp.status_code == 200
    assert any(j["id"] == job["id"] for j in resp.json())

    # Single-job GET
    resp = await client.get(f"/jobs/{job['id']}")
    assert resp.status_code == 200

    # Worker applies
    resp = await client.post(
        f"/jobs/{job['id']}/apply", json={"cover_message": "Disponible"}, headers=auth_header(worker_token)
    )
    assert resp.status_code == 201
    application = resp.json()

    # Duplicate application rejected
    resp = await client.post(
        f"/jobs/{job['id']}/apply", json={"cover_message": "Again"}, headers=auth_header(worker_token)
    )
    assert resp.status_code == 400

    # Client sees and accepts it
    resp = await client.get(f"/jobs/{job['id']}/applications", headers=auth_header(client_token))
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = await client.post(
        f"/jobs/{job['id']}/applications/{application['id']}/accept", headers=auth_header(client_token)
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "accepted"

    # Worker sees it in their own application list
    resp = await client.get("/jobs/applications/mine", headers=auth_header(worker_token))
    assert resp.status_code == 200
    mine = resp.json()
    assert len(mine) == 1
    assert mine[0]["status"] == "accepted"
    assert mine[0]["job_title"] == "Réparer une fuite d'eau"


async def test_invalid_budget_range_rejected(client: AsyncClient, admin_token: str):
    client_token = await _verified_client(client, admin_token, "budgetclient@test.tn", "20200003")
    resp = await client.post(
        "/jobs",
        json={
            "title": "Test",
            "description": "A sufficiently long description here",
            "category": "Test",
            "location": "Tunis",
            "budget_min": 100,
            "budget_max": 10,
        },
        headers=auth_header(client_token),
    )
    assert resp.status_code == 422


async def test_unverified_worker_cannot_apply(client: AsyncClient, admin_token: str):
    client_token = await _verified_client(client, admin_token, "openclient@test.tn", "20200004")
    resp = await client.post(
        "/jobs",
        json={"title": "Test", "description": "A sufficiently long description", "category": "Test", "location": "Tunis"},
        headers=auth_header(client_token),
    )
    job_id = resp.json()["id"]

    unverified_worker_token = await register_and_login(client, role="worker", email="unverified@test.tn", phone="20200005")
    resp = await client.post(
        f"/jobs/{job_id}/apply", json={"cover_message": "Hi"}, headers=auth_header(unverified_worker_token)
    )
    assert resp.status_code == 403
