"""Request logging and the analytics computed from it."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_a_successful_call_is_logged_with_its_timing(
    auth_client: TestClient, api_key: str, flush_logs
) -> None:
    auth_client.get("/v1/status", headers={"X-API-Key": api_key})
    flush_logs()

    log = auth_client.get("/api/logs").json()["items"][0]
    assert log["method"] == "GET"
    assert log["path"] == "/v1/status"
    assert log["status_code"] == 200
    assert log["error_code"] is None
    assert log["response_time_ms"] > 0
    assert log["api_key_label"].startswith("Test key (")


def test_refused_requests_are_logged_too(auth_client: TestClient, flush_logs) -> None:
    """A 429 is exactly what the owner of a key needs to see."""
    key = auth_client.post(
        "/api/keys", json={"name": "Throttled", "rate_limit_per_minute": 1}
    ).json()["key"]
    auth_client.get("/v1/status", headers={"X-API-Key": key})
    auth_client.get("/v1/status", headers={"X-API-Key": key})
    flush_logs()

    statuses = [item["status_code"] for item in auth_client.get("/api/logs").json()["items"]]
    assert statuses == [429, 200]
    rejected = auth_client.get("/api/logs", params={"status": 429}).json()["items"][0]
    assert rejected["error_code"] == "rate_limit_exceeded"


def test_an_unidentified_caller_is_not_logged(
    auth_client: TestClient, api_key: str, flush_logs
) -> None:
    """With no valid key there is no account to attribute the request to."""
    auth_client.get("/v1/status")
    auth_client.get("/v1/status", headers={"X-API-Key": "dev_live_nope"})
    flush_logs()

    assert auth_client.get("/api/logs").json()["total"] == 0


def test_logs_can_be_filtered(auth_client: TestClient, api_key: str, flush_logs) -> None:
    auth_client.get("/v1/status", headers={"X-API-Key": api_key})
    auth_client.post(
        "/v1/process", json={"text": "hi", "operation": "upper"}, headers={"X-API-Key": api_key}
    )
    auth_client.get("/v1/random?minimum=5&maximum=1", headers={"X-API-Key": api_key})
    flush_logs()

    assert auth_client.get("/api/logs", params={"method": "post"}).json()["total"] == 1
    assert auth_client.get("/api/logs", params={"status_class": "4xx"}).json()["total"] == 1
    key_id = auth_client.get("/api/keys").json()[0]["id"]
    assert auth_client.get("/api/logs", params={"api_key_id": key_id}).json()["total"] == 3


def test_logs_are_scoped_to_the_account(auth_client: TestClient, api_key: str, flush_logs) -> None:
    auth_client.get("/v1/status", headers={"X-API-Key": api_key})
    flush_logs()

    auth_client.post("/auth/logout")
    auth_client.cookies.clear()
    auth_client.post(
        "/auth/register", json={"email": "other@example.com", "password": "correct-horse-battery"}
    )
    assert auth_client.get("/api/logs").json()["total"] == 0


def test_last_used_at_is_refreshed_from_the_log_batch(
    auth_client: TestClient, api_key: str, flush_logs
) -> None:
    assert auth_client.get("/api/keys").json()[0]["last_used_at"] is None

    auth_client.get("/v1/status", headers={"X-API-Key": api_key})
    flush_logs()

    assert auth_client.get("/api/keys").json()[0]["last_used_at"] is not None


def test_usage_reflects_the_logs_exactly(
    auth_client: TestClient, api_key: str, flush_logs
) -> None:
    for _ in range(3):
        auth_client.get("/v1/status", headers={"X-API-Key": api_key})
    auth_client.get("/v1/random?minimum=5&maximum=1", headers={"X-API-Key": api_key})  # 400
    flush_logs()

    usage = auth_client.get("/api/usage").json()
    assert usage["requests_today"] == 4
    assert usage["requests_total"] == 4
    assert usage["success_rate"] == 75.0
    assert usage["avg_response_time_ms"] > 0
    assert usage["active_keys"] == 1
    assert len(usage["series"]) == 24
    assert sum(point["total"] for point in usage["series"]) == 4
    assert usage["top_endpoints"][0]["path"] == "/v1/status"


def test_an_empty_account_reports_zeros_not_placeholders(auth_client: TestClient) -> None:
    usage = auth_client.get("/api/usage").json()
    assert usage["requests_today"] == 0
    assert usage["success_rate"] is None
    assert usage["avg_response_time_ms"] is None
    assert all(point["total"] == 0 for point in usage["series"])
