"""Account registration, login and the closed management API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests.conftest import PASSWORD

PROTECTED = ["/auth/me", "/api/keys", "/api/logs", "/api/usage"]


@pytest.mark.parametrize("path", PROTECTED)
def test_management_routes_require_a_session(client: TestClient, path: str) -> None:
    response = client.get(path)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"


def test_register_normalises_the_email_and_issues_a_cookie(client: TestClient) -> None:
    response = client.post(
        "/auth/register", json={"email": " Dev@Example.COM ", "password": PASSWORD}
    )
    assert response.status_code == 201
    assert response.json()["email"] == "dev@example.com"
    assert "HttpOnly" in response.headers["set-cookie"]
    assert client.get("/auth/me").status_code == 200


def test_password_is_stored_as_a_scrypt_hash(auth_client: TestClient) -> None:
    from sqlalchemy import select

    from app.db.session import SessionLocal
    from app.models import User

    with SessionLocal() as db:
        user = db.execute(select(User)).scalar_one()
    assert user.password_hash.startswith("scrypt$")
    assert PASSWORD not in user.password_hash
    assert "password" not in auth_client.get("/auth/me").json()


def test_duplicate_registration_is_refused(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/auth/register", json={"email": "dev@example.com", "password": PASSWORD}
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "email_taken"


def test_login_gives_the_same_answer_for_both_failures(auth_client: TestClient) -> None:
    wrong = auth_client.post(
        "/auth/login", json={"email": "dev@example.com", "password": "wrong-password"}
    )
    unknown = auth_client.post(
        "/auth/login", json={"email": "nobody@example.com", "password": PASSWORD}
    )
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


def test_login_and_logout(auth_client: TestClient) -> None:
    assert auth_client.post(
        "/auth/login", json={"email": "dev@example.com", "password": PASSWORD}
    ).status_code == 200
    assert auth_client.post("/auth/logout").status_code == 204
    auth_client.cookies.clear()
    assert auth_client.get("/auth/me").status_code == 401


def test_a_tampered_session_is_rejected(auth_client: TestClient) -> None:
    auth_client.cookies.set("amp_session", "not.a.jwt")
    assert auth_client.get("/auth/me").status_code == 401


def test_validation_errors_use_the_common_envelope(client: TestClient) -> None:
    response = client.post("/auth/register", json={"email": "nope", "password": "short"})
    assert response.status_code == 422
    body = response.json()["error"]
    assert body["code"] == "validation_error"
    assert {field["field"] for field in body["fields"]} == {"email", "password"}
