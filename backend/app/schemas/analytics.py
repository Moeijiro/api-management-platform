from __future__ import annotations

from pydantic import BaseModel


class UsagePoint(BaseModel):
    """One bucket of the requests-over-time chart."""

    bucket: str          # ISO timestamp at the start of the bucket
    total: int
    errors: int


class EndpointUsage(BaseModel):
    path: str
    method: str
    requests: int
    avg_response_time_ms: float


class UsageOverview(BaseModel):
    """Dashboard tiles. Every figure is a query over this account's own logs."""

    requests_today: int
    requests_this_month: int
    requests_total: int
    success_rate: float | None
    avg_response_time_ms: float | None
    active_keys: int
    total_keys: int
    rate_limited_today: int
    series: list[UsagePoint]
    top_endpoints: list[EndpointUsage]
