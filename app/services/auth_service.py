"""Auth service — register, login, refresh.

Business rules live here; repository calls are the only DB touch points.
"""

from __future__ import annotations

import jwt
from fastapi import HTTPException, status
from sqlmodel import Session

from app.core.security import create_token, decode_token, hash_password, verify_password
from app.repositories.user_repo import create_user, get_user_by_email
from app.schemas.auth import AccessTokenResponse, TokenResponse


def register(db: Session, email: str, password: str) -> TokenResponse:
    if get_user_by_email(db, email) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    user = create_user(db, email=email, hashed_password=hash_password(password))
    return _issue_tokens(str(user.id))


def login(db: Session, email: str, password: str) -> TokenResponse:
    user = get_user_by_email(db, email)
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )
    return _issue_tokens(str(user.id))


def refresh_access_token(refresh_token: str) -> AccessTokenResponse:
    try:
        user_id = decode_token(refresh_token, expected_type="refresh")
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        ) from exc
    return AccessTokenResponse(access_token=create_token(user_id, "access"))


def _issue_tokens(user_id: str) -> TokenResponse:
    return TokenResponse(
        access_token=create_token(user_id, "access"),
        refresh_token=create_token(user_id, "refresh"),
    )
