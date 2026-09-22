"""One error shape for the whole API.

Every failure -- raised by us, by FastAPI's validation, or unexpectedly --
leaves through these handlers as:

    {"error": {"code": "invalid_api_key", "message": "…"}}

Clients can branch on ``code``; ``message`` is safe to show a human. Nothing
from the database or the traceback ever reaches the response.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings

logger = logging.getLogger("api.errors")


class APIError(Exception):
    """An error with a stable machine-readable code."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.headers = headers or {}


def error_body(code: str, message: str, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"error": {"code": code, "message": message}}
    payload["error"].update(extra)
    return payload


def error_response(
    code: str, message: str, status_code: int, headers: dict[str, str] | None = None, **extra: Any
) -> JSONResponse:
    return JSONResponse(error_body(code, message, **extra), status_code, headers=headers)


# Default codes for status codes raised as plain HTTPExceptions.
STATUS_CODES = {
    400: "bad_request",
    401: "unauthenticated",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    413: "payload_too_large",
    422: "validation_error",
    429: "rate_limit_exceeded",
}


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(APIError)
    async def _api_error(_: Request, exc: APIError) -> JSONResponse:
        return error_response(exc.code, exc.message, exc.status_code, exc.headers)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else "Request failed."
        code = STATUS_CODES.get(exc.status_code, "error")
        headers = dict(exc.headers or {})
        return error_response(code, detail, exc.status_code, headers)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        # Field paths help the caller fix the request; raw input is not echoed.
        fields = [
            {
                "field": ".".join(str(part) for part in error["loc"][1:]) or "body",
                "message": error["msg"],
            }
            for error in exc.errors()
        ]
        return error_response(
            "validation_error",
            "The request body failed validation.",
            status.HTTP_422_UNPROCESSABLE_CONTENT
            if hasattr(status, "HTTP_422_UNPROCESSABLE_CONTENT")
            else 422,
            fields=fields,
        )

    @app.exception_handler(Exception)
    async def _unexpected(request: Request, exc: Exception) -> JSONResponse:
        # Logged in full server side, described in one generic line to the client.
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        message = "An unexpected error occurred."
        if settings.debug_errors:
            message = f"{message} ({type(exc).__name__})"
        return error_response("internal_error", message, 500)
