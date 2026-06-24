"""Auth primitives: password hashing (argon2) and JWT signing/verification.

Design notes:
- argon2id via argon2-cffi; verify() is constant-time by design.
- JWT access token (short-lived) and refresh token (long-lived) carry
  separate `type` claims so they cannot be swapped.
- JWT_SECRET comes from env; never hard-coded here.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Literal

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.config import get_settings

_ph = PasswordHasher()  # argon2id, default parameters (RFC 9106 recommended)

TokenType = Literal["access", "refresh"]


# ── Password ──────────────────────────────────────────────────────────────────


def hash_password(plain: str) -> str:
    """Return an argon2id hash of *plain*."""
    return _ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Constant-time compare; returns False instead of raising on mismatch."""
    try:
        return _ph.verify(hashed, plain)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


# ── JWT ───────────────────────────────────────────────────────────────────────


def _now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


def create_token(subject: str, token_type: TokenType) -> str:
    """Issue a signed JWT for *subject* (user email or id as str)."""
    cfg = get_settings()
    if token_type == "access":
        expire = _now_utc() + timedelta(minutes=cfg.access_token_expire_minutes)
    else:
        expire = _now_utc() + timedelta(days=cfg.refresh_token_expire_days)

    payload: dict = {
        "sub": subject,
        "type": token_type,
        "exp": expire,
        "iat": _now_utc(),
        "jti": secrets.token_hex(16),  # prevent token replay after revocation (future)
    }
    return jwt.encode(payload, cfg.jwt_secret, algorithm=cfg.jwt_algorithm)


def decode_token(token: str, expected_type: TokenType) -> str:
    """Decode and validate a JWT.  Returns the *sub* claim (user id as str).

    Raises:
        jwt.ExpiredSignatureError  — token is expired
        jwt.InvalidTokenError      — any other validation failure (tampered, wrong type…)
    """
    cfg = get_settings()
    payload = jwt.decode(token, cfg.jwt_secret, algorithms=[cfg.jwt_algorithm])
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError(
            f"Expected token type '{expected_type}', got '{payload.get('type')}'"
        )
    sub = payload.get("sub")
    if not sub:
        raise jwt.InvalidTokenError("Token missing 'sub' claim")
    return str(sub)
