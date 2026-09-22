"""API key lifecycle: created once, hashed at rest, revocable, deletable."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_a_created_key_is_returned_once(auth_client: TestClient) -> None:
    created = auth_client.post("/api/keys", json={"name": "Production"}).json()
    assert created["key"].startswith("dev_live_")
    assert created["prefix"] == created["key"][:15]
    assert created["rate_limit_per_minute"] == 60

    listed = auth_client.get("/api/keys").json()[0]
    assert "key" not in listed
    assert listed["prefix"] == created["prefix"]


def test_only_a_digest_is_stored(auth_client: TestClient) -> None:
    import hashlib

    from sqlalchemy import select

    from app.db.session import SessionLocal
    from app.models import APIKey

    created = auth_client.post("/api/keys", json={"name": "Production"}).json()
    with SessionLocal() as db:
        stored = db.execute(select(APIKey)).scalar_one()

    assert stored.hashed_key == hashlib.sha256(created["key"].encode()).hexdigest()
    assert created["key"] not in stored.hashed_key


def test_a_custom_rate_limit_is_honoured(auth_client: TestClient) -> None:
    created = auth_client.post(
        "/api/keys", json={"name": "Slow", "rate_limit_per_minute": 5}
    ).json()
    assert created["rate_limit_per_minute"] == 5

    response = auth_client.get("/v1/status", headers={"X-API-Key": created["key"]})
    assert response.headers["X-RateLimit-Limit"] == "5"


def test_revoking_keeps_the_row_but_stops_the_key(
    auth_client: TestClient, api_key: str
) -> None:
    key_id = auth_client.get("/api/keys").json()[0]["id"]
    assert auth_client.get("/v1/status", headers={"X-API-Key": api_key}).status_code == 200

    revoked = auth_client.post(f"/api/keys/{key_id}/revoke").json()
    assert revoked["enabled"] is False
    assert revoked["revoked_at"] is not None

    refused = auth_client.get("/v1/status", headers={"X-API-Key": api_key})
    assert refused.status_code == 401
    assert refused.json()["error"]["code"] == "invalid_api_key"

    # The key is still listed, so its history stays explainable.
    assert len(auth_client.get("/api/keys").json()) == 1


def test_revoking_twice_is_refused(auth_client: TestClient, api_key: str) -> None:
    key_id = auth_client.get("/api/keys").json()[0]["id"]
    auth_client.post(f"/api/keys/{key_id}/revoke")
    second = auth_client.post(f"/api/keys/{key_id}/revoke")
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "already_revoked"


def test_deleting_a_key_keeps_its_request_logs(
    auth_client: TestClient, api_key: str, flush_logs
) -> None:
    key_id = auth_client.get("/api/keys").json()[0]["id"]
    auth_client.get("/v1/status", headers={"X-API-Key": api_key})
    flush_logs()

    assert auth_client.delete(f"/api/keys/{key_id}").status_code == 204
    assert auth_client.get("/api/keys").json() == []

    logs = auth_client.get("/api/logs").json()
    assert logs["total"] == 1
    assert logs["items"][0]["api_key_id"] is None       # foreign key nulled
    assert logs["items"][0]["api_key_label"] is not None  # label survives


def test_keys_of_another_account_are_not_reachable(
    auth_client: TestClient, api_key: str
) -> None:
    key_id = auth_client.get("/api/keys").json()[0]["id"]
    auth_client.post("/auth/logout")
    auth_client.cookies.clear()
    auth_client.post(
        "/auth/register", json={"email": "other@example.com", "password": "correct-horse-battery"}
    )

    # 404, not 403: the API does not confirm that the id exists.
    assert auth_client.post(f"/api/keys/{key_id}/revoke").status_code == 404
    assert auth_client.delete(f"/api/keys/{key_id}").status_code == 404


def test_the_active_key_limit_is_enforced(auth_client: TestClient) -> None:
    for index in range(10):
        assert auth_client.post("/api/keys", json={"name": f"Key {index}"}).status_code == 201

    eleventh = auth_client.post("/api/keys", json={"name": "Too many"})
    assert eleventh.status_code == 409
    assert eleventh.json()["error"]["code"] == "key_limit_reached"
