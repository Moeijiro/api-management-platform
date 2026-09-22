"""One row per call to the protected API.

Written by a background batch writer, never on the request path. The columns
are what an operator needs to answer "what happened and how fast" -- request
bodies are deliberately not stored.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, utcnow


class RequestLog(Base):
    __tablename__ = "request_logs"
    __table_args__ = (
        # The three queries the dashboard actually runs: a user's recent calls,
        # one key's usage, and status breakdowns over a time window.
        Index("ix_logs_user_created", "user_id", "created_at"),
        Index("ix_logs_key_created", "api_key_id", "created_at"),
        Index("ix_logs_status_created", "status_code", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    # Kept when the key is deleted, so history does not disappear with it.
    api_key_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("api_keys.id", ondelete="SET NULL"), default=None
    )
    api_key_label: Mapped[Optional[str]] = mapped_column(String(96), default=None)

    method: Mapped[str] = mapped_column(String(8))
    path: Mapped[str] = mapped_column(String(255))
    status_code: Mapped[int] = mapped_column(Integer)
    # Microseconds, not milliseconds: a fast endpoint answers in well under a
    # millisecond, and rounding those to 0 would make the averages useless.
    response_time_us: Mapped[int] = mapped_column(Integer)
    client_ip: Mapped[Optional[str]] = mapped_column(String(45), default=None)
    # Set when the request was refused before the endpoint ran.
    error_code: Mapped[Optional[str]] = mapped_column(String(48), default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )
