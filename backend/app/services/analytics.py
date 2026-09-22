"""Usage analytics, computed from the request log table.

Nothing here is estimated or cached: an account with no traffic sees zeros.
The time series is grouped in the database rather than in Python, using the
expression the current dialect supports.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import Select, case, func, select
from sqlalchemy.orm import Session

from app.models import APIKey, RequestLog

SERIES_HOURS = 24


def _hour_bucket(db: Session):
    """Truncate ``created_at`` to the hour, portably.

    SQLite has no date_trunc and PostgreSQL has no strftime, so the expression
    is chosen from the bind's dialect instead of assuming one database.
    """
    if db.bind.dialect.name == "sqlite":
        return func.strftime("%Y-%m-%dT%H:00:00", RequestLog.created_at)
    return func.to_char(func.date_trunc("hour", RequestLog.created_at), "YYYY-MM-DD\"T\"HH24:00:00")


def _mine(user_id: int) -> Select:
    return select(RequestLog).where(RequestLog.user_id == user_id)


def overview(db: Session, user_id: int) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_month = start_of_day.replace(day=1)
    series_start = (now - timedelta(hours=SERIES_HOURS - 1)).replace(
        minute=0, second=0, microsecond=0
    )

    def count(*conditions) -> int:
        return db.execute(
            select(func.count())
            .select_from(RequestLog)
            .where(RequestLog.user_id == user_id, *conditions)
        ).scalar_one()

    total = count()
    successes = count(RequestLog.status_code < 400)
    avg_us = db.execute(
        select(func.avg(RequestLog.response_time_us)).where(RequestLog.user_id == user_id)
    ).scalar_one()

    bucket = _hour_bucket(db)
    series_rows = db.execute(
        select(
            bucket.label("bucket"),
            func.count().label("total"),
            func.sum(case((RequestLog.status_code >= 400, 1), else_=0)).label("errors"),
        )
        .where(RequestLog.user_id == user_id, RequestLog.created_at >= series_start)
        .group_by("bucket")
        .order_by("bucket")
    ).all()
    counted = {row.bucket: (row.total, int(row.errors or 0)) for row in series_rows}

    # Empty hours are part of the picture, so the chart is filled in here.
    series = []
    for offset in range(SERIES_HOURS):
        moment = series_start + timedelta(hours=offset)
        label = moment.strftime("%Y-%m-%dT%H:00:00")
        hits, errors = counted.get(label, (0, 0))
        series.append({"bucket": label, "total": hits, "errors": errors})

    top = db.execute(
        select(
            RequestLog.path,
            RequestLog.method,
            func.count().label("requests"),
            func.avg(RequestLog.response_time_us).label("avg_us"),
        )
        .where(RequestLog.user_id == user_id)
        .group_by(RequestLog.path, RequestLog.method)
        .order_by(func.count().desc())
        .limit(5)
    ).all()

    keys_total = db.execute(
        select(func.count()).select_from(APIKey).where(APIKey.user_id == user_id)
    ).scalar_one()
    keys_active = db.execute(
        select(func.count())
        .select_from(APIKey)
        .where(APIKey.user_id == user_id, APIKey.enabled.is_(True))
    ).scalar_one()

    return {
        "requests_today": count(RequestLog.created_at >= start_of_day),
        "requests_this_month": count(RequestLog.created_at >= start_of_month),
        "requests_total": total,
        "success_rate": round(successes / total * 100, 1) if total else None,
        "avg_response_time_ms": round(avg_us / 1000, 2) if avg_us is not None else None,
        "active_keys": keys_active,
        "total_keys": keys_total,
        "rate_limited_today": count(
            RequestLog.status_code == 429, RequestLog.created_at >= start_of_day
        ),
        "series": series,
        "top_endpoints": [
            {
                "path": row.path,
                "method": row.method,
                "requests": row.requests,
                "avg_response_time_ms": round((row.avg_us or 0) / 1000, 2),
            }
            for row in top
        ],
    }
