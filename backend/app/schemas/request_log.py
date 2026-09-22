from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, computed_field, field_serializer

from app.schemas.common import utc_iso


class RequestLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    api_key_id: int | None
    api_key_label: str | None
    method: str
    path: str
    status_code: int
    response_time_us: int
    client_ip: str | None
    error_code: str | None
    created_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def response_time_ms(self) -> float:
        return round(self.response_time_us / 1000, 2)

    @field_serializer("created_at")
    def _as_utc(self, value: datetime) -> str | None:
        return utc_iso(value)


class RequestLogPage(BaseModel):
    items: list[RequestLogOut]
    total: int
    limit: int
    offset: int
