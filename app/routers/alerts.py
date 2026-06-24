"""Alerts router: GET /alerts (paginated, newest first)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.deps import CurrentUser, get_db
from app.repositories.alert_repo import list_alerts
from app.schemas.alert import AlertResponse

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertResponse])
def get_alerts(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list:
    return list_alerts(db, user_id=current_user.id, offset=offset, limit=limit)  # type: ignore[arg-type]
