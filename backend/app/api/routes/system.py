"""Health and service metadata."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.services.request_log import writer

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health", summary="Liveness")
def health(db: Session = Depends(get_db)) -> dict[str, object]:
    try:
        db.execute(text("SELECT 1"))
        database_ok = True
    except Exception:  # pragma: no cover - only on a broken DB
        database_ok = False

    return {
        "status": "ok" if database_ok else "degraded",
        "database": "ok" if database_ok else "unavailable",
        "environment": settings.environment,
        "default_rate_limit_per_minute": settings.default_rate_limit_per_minute,
        "log_writer": {"written": writer.written, "dropped": writer.dropped},
    }
