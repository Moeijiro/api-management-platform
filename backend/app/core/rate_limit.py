"""Per-key rate limiting.

A sliding window over the last 60 seconds, held in process. That is the right
size for a single-instance deployment and keeps the default install free of
Redis; ``RateLimiter`` is a small interface, so swapping in a Redis-backed
implementation later touches this file only.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass

WINDOW_SECONDS = 60


@dataclass(slots=True)
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    reset_after: int          # seconds until the window frees a slot
    retry_after: int | None = None

    @property
    def headers(self) -> dict[str, str]:
        """The headers every response carries, rejected or not."""
        headers = {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(max(0, self.remaining)),
            "X-RateLimit-Reset": str(self.reset_after),
        }
        if self.retry_after is not None:
            headers["Retry-After"] = str(self.retry_after)
        return headers


class SlidingWindowRateLimiter:
    """Counts the timestamps of the last ``WINDOW_SECONDS`` per key."""

    def __init__(self, window_seconds: int = WINDOW_SECONDS) -> None:
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str, limit: int) -> RateLimitResult:
        now = time.monotonic()
        hits = self._hits[key]

        # Drop everything that has fallen out of the window.
        cutoff = now - self.window
        while hits and hits[0] <= cutoff:
            hits.popleft()

        if len(hits) >= limit:
            retry_after = max(1, int(self.window - (now - hits[0])) + 1)
            return RateLimitResult(
                allowed=False,
                limit=limit,
                remaining=0,
                reset_after=retry_after,
                retry_after=retry_after,
            )

        hits.append(now)
        reset_after = max(1, int(self.window - (now - hits[0]))) if hits else self.window
        return RateLimitResult(
            allowed=True,
            limit=limit,
            remaining=max(0, limit - len(hits)),
            reset_after=reset_after,
        )

    def reset(self, key: str | None = None) -> None:
        """Clear one key's window, or all of them (used by the test suite)."""
        if key is None:
            self._hits.clear()
        else:
            self._hits.pop(key, None)


limiter = SlidingWindowRateLimiter()
