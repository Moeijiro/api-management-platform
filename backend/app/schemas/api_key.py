from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.schemas.common import utc_iso


class APIKeyCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=64)
    rate_limit_per_minute: int | None = Field(
        default=None, ge=1, le=100_000, description="Defaults to the application setting."
    )


class APIKeyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    prefix: str
    enabled: bool
    rate_limit_per_minute: int
    created_at: datetime
    last_used_at: datetime | None
    revoked_at: datetime | None

    @field_serializer("created_at", "last_used_at", "revoked_at")
    def _as_utc(self, value: datetime | None) -> str | None:
        return utc_iso(value)

    @property
    def status(self) -> str:  # pragma: no cover - convenience for templates
        return "active" if self.enabled and self.revoked_at is None else "revoked"


class APIKeyCreated(APIKeyOut):
    """Returned once, by the create call only."""

    key: str
    warning: str = (
        "Copy this key now — only a hash is stored, so it cannot be shown again."
    )
