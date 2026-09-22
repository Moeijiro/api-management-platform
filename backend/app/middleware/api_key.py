"""API key authentication, rate limiting and logging for the public API.

One pass over every request under ``/v1``:

    extract key → hash → look up → check active → check quota
      → run the endpoint → attach quota headers → queue the log

Rejections are logged too: a 401 or a 429 is exactly the kind of thing the
owner of a key needs to see in the dashboard.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings
from app.core.errors import error_response
from app.core.rate_limit import RateLimitResult, limiter
from app.core.security import API_KEY_HEADER, hash_api_key
from app.db.session import SessionLocal
from app.models import APIKey
from app.services.request_log import writer


@dataclass(slots=True)
class KeyContext:
    """What the endpoint is allowed to know about the caller."""

    id: int
    user_id: int
    name: str
    prefix: str
    rate_limit_per_minute: int


class APIKeyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, protected_prefix: str = "/v1") -> None:
        super().__init__(app)
        self.prefix = protected_prefix

    async def dispatch(self, request: Request, call_next) -> Response:  # noqa: ANN001
        if not request.url.path.startswith(self.prefix):
            return await call_next(request)

        started = time.perf_counter()
        raw_key = request.headers.get(API_KEY_HEADER, "").strip()

        if not raw_key:
            return self._reject(
                request,
                started,
                code="missing_api_key",
                message=f"Provide your API key in the {API_KEY_HEADER} header.",
                status_code=401,
            )

        # The digest is the lookup key; the raw value is never compared or stored.
        context = await asyncio.to_thread(self._lookup, hash_api_key(raw_key))
        if context is None:
            return self._reject(
                request,
                started,
                code="invalid_api_key",
                message="The supplied API key is invalid or has been revoked.",
                status_code=401,
            )

        quota = limiter.check(f"key:{context.id}", context.rate_limit_per_minute)
        if not quota.allowed:
            return self._reject(
                request,
                started,
                code="rate_limit_exceeded",
                message=(
                    f"Rate limit of {quota.limit} requests per minute exceeded for this "
                    "API key."
                ),
                status_code=429,
                context=context,
                quota=quota,
            )

        request.state.api_key = context
        response = await call_next(request)

        for header, value in quota.headers.items():
            response.headers[header] = value

        self._log(request, started, response.status_code, context=context)
        return response

    # -- helpers -----------------------------------------------------------
    @staticmethod
    def _lookup(digest: str) -> KeyContext | None:
        """Runs in a worker thread: the ORM session here is synchronous."""
        with SessionLocal() as db:
            key = db.execute(
                select(APIKey).where(APIKey.hashed_key == digest)
            ).scalar_one_or_none()
            if key is None or not key.active:
                return None
            return KeyContext(
                id=key.id,
                user_id=key.user_id,
                name=key.name,
                prefix=key.prefix,
                rate_limit_per_minute=key.rate_limit_per_minute,
            )

    def _reject(
        self,
        request: Request,
        started: float,
        *,
        code: str,
        message: str,
        status_code: int,
        context: KeyContext | None = None,
        quota: RateLimitResult | None = None,
    ) -> Response:
        headers = quota.headers if quota else {}
        response = error_response(code, message, status_code, headers)
        # An unidentified caller has no key to attribute the log to.
        if context is not None:
            self._log(request, started, status_code, context=context, error_code=code)
        return response

    @staticmethod
    def _log(
        request: Request,
        started: float,
        status_code: int,
        *,
        context: KeyContext,
        error_code: str | None = None,
    ) -> None:
        writer.submit(
            {
                "user_id": context.user_id,
                "api_key_id": context.id,
                "api_key_label": f"{context.name} ({context.prefix})",
                "method": request.method,
                "path": request.url.path[:255],
                "status_code": status_code,
                "response_time_ms": int((time.perf_counter() - started) * 1000),
                "client_ip": _client_ip(request) if settings.log_client_ip else None,
                "error_code": error_code,
            }
        )


def _client_ip(request: Request) -> str | None:
    """Behind a proxy the first X-Forwarded-For entry is the real client."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()[:45]
    return request.client.host if request.client else None
