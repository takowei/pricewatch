"""Users router: /users/me GET + PATCH."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.deps import CurrentUser, get_db
from app.models.user import User
from app.repositories.user_repo import update_user
from app.schemas.user import UserResponse, UserUpdateRequest

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_me(current_user: CurrentUser) -> User:
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_me(
    body: UserUpdateRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> User:
    updates = body.model_dump(exclude_none=True)
    if not updates:
        return current_user
    return update_user(db, current_user, **updates)
