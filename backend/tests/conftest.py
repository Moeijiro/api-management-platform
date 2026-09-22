"""Test fixtures.

The environment is configured before the app is imported: settings, the engine
and the rate limiter are all resolved once at import time.
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator

import pytest

TEST_DB = os.path.join(tempfile.mkdtemp(prefix="amp-tests-"), "test.db")
os.environ.update(
    ENVIRONMENT="development",
    DATABASE_URL=f"sqlite:///{TEST_DB}",
    SECRET_KEY="test-secret-not-used-anywhere-else-0123456789",
    ALLOW_REGISTRATION="true",
    DEFAULT_RATE_LIMIT_PER_MINUTE="60",
    # Flush logs as soon as they are queued so assertions do not race the writer.
    LOG_FLUSH_INTERVAL_SECONDS="0.01",
    LOG_BATCH_SIZE="10",
)

from fastapi.testclient import TestClient  # noqa: E402

from app.core.rate_limit import limiter  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.main import app  # noqa: E402
from app.services.request_log import writer  # noqa: E402

PASSWORD = "correct-horse-battery"


@pytest.fixture(autouse=True)
def fresh_state() -> Iterator[None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    limiter.reset()
    yield


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app, base_url="http://localhost:8000") as test_client:
        yield test_client


@pytest.fixture
def auth_client(client: TestClient) -> TestClient:
    """A registered account holding its session cookie."""
    response = client.post(
        "/auth/register", json={"email": "dev@example.com", "password": PASSWORD}
    )
    assert response.status_code == 201, response.text
    return client


@pytest.fixture
def api_key(auth_client: TestClient) -> str:
    """A usable raw API key (returned only by the create call)."""
    return auth_client.post("/api/keys", json={"name": "Test key"}).json()["key"]


@pytest.fixture
def flush_logs(client: TestClient):
    """Wait until the background writer has persisted everything queued."""

    def _flush() -> None:
        client.portal.call(writer.flush)

    return _flush
