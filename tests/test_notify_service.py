"""Unit tests for notify_service — Telegram HTTP call is mocked."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from sqlmodel import Session

from app.repositories.alert_repo import create_alert_if_new
from app.services.notify_service import _build_message, notify_pending_alerts
from tests.factories import make_product, make_user, make_watchlist


def test_build_message_at_target(db: Session):
    from app.models.alert import Alert

    alert = Alert(
        user_id=1,
        watchlist_id=1,
        product_id=1,
        triggered_price=590,
        reason="at_target",
    )
    msg = _build_message(alert, "Slim Fit Pants")
    assert "達標" in msg
    assert "590" in msg
    assert "Slim Fit Pants" in msg


def test_build_message_price_drop(db: Session):
    from app.models.alert import Alert

    alert = Alert(
        user_id=1,
        watchlist_id=1,
        product_id=1,
        triggered_price=490,
        reason="price_drop",
    )
    msg = _build_message(alert, "Wide Pants")
    assert "降價" in msg
    assert "490" in msg


def test_notify_skipped_when_no_token(db: Session):
    """notify_pending_alerts returns 0 immediately when token is empty."""
    with patch("app.services.notify_service.get_settings") as mock_cfg:
        mock_cfg.return_value = MagicMock(telegram_bot_token="", telegram_chat_id="")
        result = notify_pending_alerts(db)
    assert result == 0


def test_notify_sends_pending_and_marks_notified(db: Session):
    """Creates an unnotified alert and verifies Telegram is called once."""
    user = make_user(db, email="tg@b.com")
    wl = make_watchlist(db, user_id=user.id, keyword="Pants")
    product = make_product(db, product_url="https://example.com/tg-p")

    create_alert_if_new(
        db,
        user_id=user.id,
        watchlist_id=wl.id,
        product_id=product.id,
        triggered_price=590,
        reason="at_target",
    )

    with (
        patch("app.services.notify_service.get_settings") as mock_cfg,
        patch("app.services.notify_service._send_telegram", return_value=True) as mock_send,
    ):
        mock_cfg.return_value = MagicMock(
            telegram_bot_token="fake-token",
            telegram_chat_id="12345",
        )
        # patch get_user_by_id to return user with no per-user chat_id
        with patch("app.services.notify_service.get_user_by_id", return_value=user):
            sent = notify_pending_alerts(db)

    assert sent == 1
    mock_send.assert_called_once()

    # Alert should now be marked is_notified=True
    from sqlmodel import select

    from app.models.alert import Alert

    alerts = list(db.exec(select(Alert)).all())
    assert len(alerts) == 1
    assert alerts[0].is_notified is True


def test_notify_skips_alert_already_notified(db: Session):
    """Alerts with is_notified=True are not re-sent."""
    user = make_user(db, email="tg2@b.com")
    wl = make_watchlist(db, user_id=user.id, keyword="Shirt")
    product = make_product(db, product_url="https://example.com/tg2-p")

    alert = create_alert_if_new(
        db,
        user_id=user.id,
        watchlist_id=wl.id,
        product_id=product.id,
        triggered_price=490,
        reason="price_drop",
    )
    # Mark as already notified
    from app.repositories.alert_repo import mark_notified

    mark_notified(db, alert.id)

    with (
        patch("app.services.notify_service.get_settings") as mock_cfg,
        patch("app.services.notify_service._send_telegram", return_value=True) as mock_send,
    ):
        mock_cfg.return_value = MagicMock(
            telegram_bot_token="fake-token",
            telegram_chat_id="12345",
        )
        sent = notify_pending_alerts(db)

    assert sent == 0
    mock_send.assert_not_called()
