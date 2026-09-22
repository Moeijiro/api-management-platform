"""Housekeeping for the request log table."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import RequestLog

logger = logging.getLogger("api.maintenance")


def purge_old_logs(db: Session, retention_days: int | None = None) -> int:
    """Delete logs older than the retention window. Returns the row count.

    Kept as a command rather than a background job: on this scale a cron entry
    or a manual run is honest, and a scheduler would be one more moving part.
    """
    days = settings.log_retention_days if retention_days is None else retention_days
    if days <= 0:
        return 0

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    result = db.execute(delete(RequestLog).where(RequestLog.created_at < cutoff))
    db.commit()
    deleted = result.rowcount or 0
    logger.info("Purged %s request logs older than %s days", deleted, days)
    return deleted
