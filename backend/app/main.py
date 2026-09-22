"""FastAPI application entry point."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import analytics, auth, demo, keys, logs, system
from app.core.config import settings
from app.core.errors import install_error_handlers
from app.core.security import API_KEY_HEADER
from app.db.session import init_db
from app.middleware.api_key import APIKeyMiddleware
from app.services.request_log import writer

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)-8s %(name)s: %(message)s"
)
logger = logging.getLogger("app")

DESCRIPTION = f"""
A small API platform: issue keys, call a protected API with them, and see what
happened.

* **`/v1/*`** is the protected API. Send your key as `{API_KEY_HEADER}`.
  Every request is authenticated, rate limited and logged.
* **`/api/*`** is the management API, used by the dashboard and authenticated
  with a session cookie. API keys cannot reach it.
* Errors always look like `{{"error": {{"code": "...", "message": "..."}}}}`.
"""


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    await writer.start()
    logger.info(
        "API Management Platform ready (environment=%s, default limit=%s/min)",
        settings.environment,
        settings.default_rate_limit_per_minute,
    )
    yield
    # Flush whatever is queued before the process exits.
    await writer.stop()


app = FastAPI(
    title="API Management Platform",
    description=DESCRIPTION,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Order matters: CORS is added last so it wraps everything, including the
# responses the API key middleware returns on its own.
app.add_middleware(APIKeyMiddleware, protected_prefix="/v1")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", API_KEY_HEADER],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
)

install_error_handlers(app)

app.include_router(system.router)
app.include_router(auth.router)
app.include_router(keys.router)
app.include_router(logs.router)
app.include_router(analytics.router)
app.include_router(demo.router)


@app.get("/", include_in_schema=False)
def index() -> JSONResponse:
    return JSONResponse(
        {
            "service": "api-management-platform",
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/api/health",
        }
    )
