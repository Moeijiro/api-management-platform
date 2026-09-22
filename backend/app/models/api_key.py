"""API keys.

Only a SHA-256 digest of the key is stored. The raw value exists once, in the
response that created it, and cannot be recovered afterwards.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, utcnow

if TYPE_CHECKING:
    from app.models.user import User


class APIKey(Base, TimestampMixin):
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    name: Mapped[str] = mapped_column(String(64))
    # Shown in the dashboard so two keys can be told apart, e.g. dev_live_9f3a.
    prefix: Mapped[str] = mapped_column(String(32), index=True)
    hashed_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=None
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=None
    )
    # Per-key quota; falls back to the application default when created.
    rate_limit_per_minute: Mapped[int] = mapped_column(Integer, default=60)

    user: Mapped["User"] = relationship(back_populates="api_keys")

    @property
    def active(self) -> bool:
        return self.enabled and self.revoked_at is None

    def revoke(self) -> None:
        self.enabled = False
        self.revoked_at = utcnow()
