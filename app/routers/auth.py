"""Auth router: register, login, refresh."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from app.core.deps import get_db
from app.core.rate_limit import limiter
from app.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return auth_service.register(db, email=body.email, password=body.password)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(
    request: Request,  # required by slowapi
    body: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    return auth_service.login(db, email=body.email, password=body.password)


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(body: RefreshRequest) -> AccessTokenResponse:
    return auth_service.refresh_access_token(body.refresh_token)
