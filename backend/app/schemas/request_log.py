from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, field_serializer


class RequestLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    api_key_id: int | None
    api_key_label: str | None
    method: str
    path: str
    status_code: int
    response_time_ms: int
    client_ip: str | None
    error_code: str | None
    created_at: datetime

    @field_serializer("created_at")
    def _as_utc(self, value: datetime) -> str:
        """SQLite returns naive datetimes; they are UTC, so say so."""
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()


class RequestLogPage(BaseModel):
    items: list[RequestLogOut]
    total: int
    limit: int
    offset: int
