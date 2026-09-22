"""Dashboard authentication.

The management API is session based: an HttpOnly cookie holding a signed JWT.
API keys authenticate the public API under ``/v1`` and deliberately cannot be
used to manage keys — a leaked key must not be able to mint more of them.
"""

from __future__ import annotations

from fastapi import Depends, Path, Request, status
from sqlalchemy.orm import Session

from app.core.errors import APIError
from app.core.security import SESSION_COOKIE_NAME, read_access_token
from app.db.session import get_db
from app.models import APIKey, User

UNAUTHENTICATED = APIError(
    "unauthenticated",
    "Sign in to use the management API.",
    status.HTTP_401_UNAUTHORIZED,
)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        raise UNAUTHENTICATED

    payload = read_access_token(token)
    if not payload:
        raise UNAUTHENTICATED

    user = db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise UNAUTHENTICATED
    return user


def get_owned_key(
    key_id: int = Path(ge=1),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> APIKey:
    """A key the caller owns, or 404 — never a hint that the id exists."""
    key = db.get(APIKey, key_id)
    if key is None or key.user_id != user.id:
        raise APIError("not_found", "API key not found.", status.HTTP_404_NOT_FOUND)
    return key
