"""Registration, login and the current account."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.core.errors import APIError
from app.core.security import (
    SESSION_COOKIE_NAME,
    create_access_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models import User
from app.schemas.auth import LoginRequest, RegisterRequest, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_session(response: Response, user: User) -> None:
    response.set_cookie(
        SESSION_COOKIE_NAME,
        create_access_token(user.id),
        max_age=settings.access_token_ttl_minutes * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/",
    )


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create an account",
)
def register(
    payload: RegisterRequest, response: Response, db: Session = Depends(get_db)
) -> User:
    if not settings.allow_registration:
        raise APIError(
            "registration_disabled", "Registration is closed on this instance.", 403
        )

    exists = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if exists:
        raise APIError("email_taken", "That email is already registered.", 409)

    user = User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    _issue_session(response, user)
    return user


@router.post("/login", response_model=UserOut, summary="Sign in")
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> User:
    user = db.execute(
        select(User).where(User.email == payload.email.strip().lower())
    ).scalar_one_or_none()

    # One answer for both failures: a different message would confirm which
    # addresses have accounts.
    if user is None or not verify_password(payload.password, user.password_hash):
        raise APIError("invalid_credentials", "Incorrect email or password.", 401)
    if not user.is_active:
        raise APIError("account_disabled", "This account is disabled.", 403)

    _issue_session(response, user)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Sign out")
def logout(response: Response) -> Response:
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=UserOut, summary="Current account")
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.get("/config", summary="What the sign-in screen needs to know")
def auth_config() -> dict[str, object]:
    return {
        "registration_enabled": settings.allow_registration,
        "default_rate_limit_per_minute": settings.default_rate_limit_per_minute,
    }
