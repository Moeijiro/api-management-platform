"""Shared serialisation helpers."""

from __future__ import annotations

from datetime import datetime, timezone


def utc_iso(value: datetime | None) -> str | None:
    """Serialise a timestamp as explicit UTC.

    SQLite (and ``func.now()``) hand back naive datetimes that are UTC. Sent
    without a zone, a browser parses them as local time, which is how a key
    created a second ago ends up displayed as "3 hours ago".
    """
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()
