"""Password hashing, dashboard sessions and API key material."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.core.config import settings

SESSION_COOKIE_NAME = "amp_session"
API_KEY_HEADER = "X-API-Key"
JWT_ALGORITHM = "HS256"

# scrypt: 128 * r * N = 16 MiB per hash. maxmem must be passed explicitly --
# OpenSSL's default ceiling is 32 MiB and rejects anything above it.
SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_LEN = 32
SCRYPT_MAXMEM = 256 * 1024 * 1024


# --------------------------------------------------------------------------
# Passwords
# --------------------------------------------------------------------------
def hash_password(password: str) -> str:
    """``scrypt$n$r$p$salt$digest`` -- the parameters travel with the hash, so
    they can be raised later without invalidating existing accounts."""
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode(),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=SCRYPT_LEN,
        maxmem=SCRYPT_MAXMEM,
    )
    return "scrypt${}${}${}${}${}".format(
        SCRYPT_N,
        SCRYPT_R,
        SCRYPT_P,
        base64.b64encode(salt).decode(),
        base64.b64encode(digest).decode(),
    )


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt_b64, digest_b64 = stored.split("$")
        if scheme != "scrypt":
            return False
        expected = base64.b64decode(digest_b64)
        digest = hashlib.scrypt(
            password.encode(),
            salt=base64.b64decode(salt_b64),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(expected),
            maxmem=SCRYPT_MAXMEM,
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(digest, expected)


# --------------------------------------------------------------------------
# Dashboard session
# --------------------------------------------------------------------------
def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.access_token_ttl_minutes)).timestamp()),
        "jti": secrets.token_urlsafe(8),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=JWT_ALGORITHM)


def read_access_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None


# --------------------------------------------------------------------------
# API keys
# --------------------------------------------------------------------------
def generate_api_key() -> tuple[str, str, str]:
    """Return ``(raw_key, prefix, digest)``.

    The key is 256 bits of entropy, so a plain SHA-256 is the right digest:
    there is nothing to brute force, and a slow KDF would tax every single
    API request. Passwords are a different story -- see ``hash_password``.
    """
    secret = secrets.token_urlsafe(32)
    raw = f"{settings.api_key_prefix}_{secret}"
    prefix = f"{settings.api_key_prefix}_{secret[:6]}"
    return raw, prefix, hash_api_key(raw)


def hash_api_key(raw: str) -> str:
    return hashlib.sha256(raw.strip().encode()).hexdigest()
