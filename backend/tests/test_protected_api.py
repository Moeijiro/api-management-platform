"""The middleware in front of /v1: authentication, quotas and logging."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.rate_limit import limiter


def test_a_valid_key_reaches_the_endpoint(auth_client: TestClient, api_key: str) -> None:
    response = auth_client.get("/v1/status", headers={"X-API-Key": api_key})
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "authenticated": True,
        "timestamp": response.json()["timestamp"],
    }


def test_every_response_carries_the_quota_headers(
    auth_client: TestClient, api_key: str
) -> None:
    first = auth_client.get("/v1/status", headers={"X-API-Key": api_key})
    second = auth_client.get("/v1/status", headers={"X-API-Key": api_key})

    assert first.headers["X-RateLimit-Limit"] == "60"
    assert int(first.headers["X-RateLimit-Remaining"]) == 59
    assert int(second.headers["X-RateLimit-Remaining"]) == 58
    assert int(first.headers["X-RateLimit-Reset"]) > 0


def test_a_missing_key_is_refused(client: TestClient) -> None:
    response = client.get("/v1/status")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "missing_api_key"


def test_an_invalid_key_is_refused_without_hinting_why(client: TestClient) -> None:
    response = client.get("/v1/status", headers={"X-API-Key": "dev_live_not-a-real-key"})
    assert response.status_code == 401
    assert response.json()["error"] == {
        "code": "invalid_api_key",
        "message": "The supplied API key is invalid or has been revoked.",
    }


def test_the_profile_endpoint_describes_the_calling_key(
    auth_client: TestClient, api_key: str
) -> None:
    body = auth_client.get("/v1/profile", headers={"X-API-Key": api_key}).json()
    assert body["key"]["name"] == "Test key"
    assert body["key"]["prefix"] == api_key[:15]
    assert body["rate_limit_per_minute"] == 60
    # The raw key is never echoed back.
    assert api_key not in str(body)


def test_process_transforms_the_payload(auth_client: TestClient, api_key: str) -> None:
    response = auth_client.post(
        "/v1/process",
        json={"text": "hello world", "operation": "word_count"},
        headers={"X-API-Key": api_key},
    )
    assert response.json()["result"] == 2


def test_the_rate_limit_returns_429_with_retry_after(auth_client: TestClient) -> None:
    key = auth_client.post(
        "/api/keys", json={"name": "Throttled", "rate_limit_per_minute": 3}
    ).json()["key"]

    codes = [
        auth_client.get("/v1/status", headers={"X-API-Key": key}).status_code
        for _ in range(4)
    ]
    assert codes == [200, 200, 200, 429]

    refused = auth_client.get("/v1/status", headers={"X-API-Key": key})
    assert refused.json()["error"]["code"] == "rate_limit_exceeded"
    assert refused.headers["X-RateLimit-Remaining"] == "0"
    assert int(refused.headers["Retry-After"]) > 0


def test_quotas_are_per_key(auth_client: TestClient) -> None:
    slow = auth_client.post(
        "/api/keys", json={"name": "Slow", "rate_limit_per_minute": 1}
    ).json()["key"]
    other = auth_client.post("/api/keys", json={"name": "Other"}).json()["key"]

    auth_client.get("/v1/status", headers={"X-API-Key": slow})
    assert auth_client.get("/v1/status", headers={"X-API-Key": slow}).status_code == 429
    assert auth_client.get("/v1/status", headers={"X-API-Key": other}).status_code == 200


def test_revoking_frees_the_window(auth_client: TestClient) -> None:
    """A revoked key's counters must not linger for the next key."""
    created = auth_client.post(
        "/api/keys", json={"name": "Temp", "rate_limit_per_minute": 1}
    ).json()
    auth_client.get("/v1/status", headers={"X-API-Key": created["key"]})
    auth_client.post(f"/api/keys/{created['id']}/revoke")
    assert limiter.check(f"key:{created['id']}", 1).allowed


def test_the_management_api_rejects_an_api_key(
    auth_client: TestClient, api_key: str
) -> None:
    """A leaked key must not be able to mint more keys."""
    auth_client.cookies.clear()  # the key is now the only credential offered
    response = auth_client.get("/api/keys", headers={"X-API-Key": api_key})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"
