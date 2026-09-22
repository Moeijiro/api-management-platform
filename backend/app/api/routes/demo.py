"""The protected demo API.

These endpoints exist to be called with an API key: they are what the
middleware authenticates, rate limits and logs. They are deliberately trivial —
the interesting behaviour is in front of them, not inside them.
"""

from __future__ import annotations

import random
import time
from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, Field

from app.core.errors import APIError
from app.middleware.api_key import KeyContext

router = APIRouter(prefix="/v1", tags=["demo api"])


def current_key(request: Request) -> KeyContext:
    """The key the middleware resolved for this request."""
    key = getattr(request.state, "api_key", None)
    if key is None:  # pragma: no cover - middleware guarantees this
        raise APIError("missing_api_key", "This endpoint requires an API key.", 401)
    return key


CurrentKey = Annotated[KeyContext, Depends(current_key)]


@router.get("/status", summary="Liveness check for the demo API")
def status_endpoint(key: CurrentKey) -> dict[str, Any]:
    return {
        "status": "ok",
        "authenticated": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/profile", summary="Who this API key belongs to")
def profile(key: CurrentKey) -> dict[str, Any]:
    return {
        "key": {"id": key.id, "name": key.name, "prefix": key.prefix},
        "rate_limit_per_minute": key.rate_limit_per_minute,
    }


class ProcessRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=2000)
    operation: str = Field(default="upper", pattern="^(upper|lower|reverse|word_count)$")


@router.post("/process", summary="Transform a string")
def process(payload: ProcessRequest, key: CurrentKey) -> dict[str, Any]:
    started = time.perf_counter()
    operations = {
        "upper": lambda text: text.upper(),
        "lower": lambda text: text.lower(),
        "reverse": lambda text: text[::-1],
        "word_count": lambda text: len(text.split()),
    }
    return {
        "operation": payload.operation,
        "result": operations[payload.operation](payload.text),
        "took_ms": round((time.perf_counter() - started) * 1000, 3),
    }


@router.get("/random", summary="A random number, for smoke tests")
def random_number(
    key: CurrentKey,
    minimum: int = 0,
    maximum: int = 100,
) -> dict[str, Any]:
    if minimum >= maximum:
        raise APIError("invalid_range", "'minimum' must be smaller than 'maximum'.", 400)
    return {"value": random.randint(minimum, maximum), "min": minimum, "max": maximum}
