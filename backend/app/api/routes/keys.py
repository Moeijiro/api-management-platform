"""API key management."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, get_owned_key
from app.core.config import settings
from app.core.errors import APIError
from app.core.rate_limit import limiter
from app.core.security import generate_api_key
from app.db.session import get_db
from app.models import APIKey, User
from app.schemas.api_key import APIKeyCreate, APIKeyCreated, APIKeyOut

router = APIRouter(prefix="/api/keys", tags=["api keys"])


@router.get("", response_model=list[APIKeyOut], summary="List API keys")
def list_keys(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[APIKey]:
    return list(
        db.execute(
            select(APIKey)
            .where(APIKey.user_id == user.id)
            .order_by(APIKey.created_at.desc())
        ).scalars().all()
    )


@router.post(
    "",
    response_model=APIKeyCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Create an API key",
)
def create_key(
    payload: APIKeyCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> APIKeyCreated:
    active = db.execute(
        select(APIKey).where(APIKey.user_id == user.id, APIKey.enabled.is_(True))
    ).scalars().all()
    if len(active) >= settings.max_keys_per_user:
        raise APIError(
            "key_limit_reached",
            f"You already have {settings.max_keys_per_user} active keys. "
            "Revoke one before creating another.",
            409,
        )

    raw, prefix, digest = generate_api_key()
    key = APIKey(
        user_id=user.id,
        name=payload.name,
        prefix=prefix,
        hashed_key=digest,
        rate_limit_per_minute=payload.rate_limit_per_minute
        or settings.default_rate_limit_per_minute,
    )
    db.add(key)
    db.commit()
    db.refresh(key)

    # `raw` is not stored anywhere: this response is the only place it exists.
    return APIKeyCreated(
        id=key.id,
        name=key.name,
        prefix=key.prefix,
        enabled=key.enabled,
        rate_limit_per_minute=key.rate_limit_per_minute,
        created_at=key.created_at,
        last_used_at=None,
        revoked_at=None,
        key=raw,
    )


@router.post(
    "/{key_id}/revoke",
    response_model=APIKeyOut,
    summary="Revoke a key but keep its history",
)
def revoke_key(
    key: APIKey = Depends(get_owned_key), db: Session = Depends(get_db)
) -> APIKey:
    if not key.active:
        raise APIError("already_revoked", "This key is already revoked.", 409)

    key.revoke()
    db.commit()
    db.refresh(key)
    limiter.reset(f"key:{key.id}")
    return key


@router.delete(
    "/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a key (its request logs are kept)",
)
def delete_key(
    key: APIKey = Depends(get_owned_key), db: Session = Depends(get_db)
) -> Response:
    limiter.reset(f"key:{key.id}")
    db.delete(key)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
