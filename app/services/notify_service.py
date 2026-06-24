"""Telegram notification service.

Design:
- Dedup is handled at the DB layer (Alert.is_notified flag).
  We only push alerts where is_notified=False, then mark them True.
- Falls back to no-op silently when TELEGRAM_BOT_TOKEN is not configured.
- Uses stdlib urllib — no additional deps.
"""

from __future__ import annotations

import logging
import urllib.parse
import urllib.request

from sqlmodel import Session, select

from app.core.config import get_settings
from app.models.alert import Alert
from app.repositories.alert_repo import mark_notified
from app.repositories.product_repo import get_product_by_id
from app.repositories.user_repo import get_user_by_id

logger = logging.getLogger(__name__)

_TG_API = "https://api.telegram.org"


def _build_message(alert: Alert, product_name: str) -> str:
    reason_label = "達標" if alert.reason == "at_target" else "降價"
    return (
        f"\U0001f514 PriceWatch 警示\n"
        f"{reason_label}：{product_name}\n"
        f"目前售價：NT${alert.triggered_price}"
    )


def _send_telegram(token: str, chat_id: str, text: str) -> bool:
    """POST to Telegram sendMessage; returns True on success."""
    url = f"{_TG_API}/bot{token}/sendMessage"
    payload = urllib.parse.urlencode(
        {"chat_id": chat_id, "text": text, "disable_web_page_preview": "true"}
    ).encode()
    try:
        with urllib.request.urlopen(url, data=payload, timeout=15) as resp:
            return resp.status == 200
    except Exception as exc:  # noqa: BLE001 — best-effort notifier
        logger.warning("Telegram send failed: %s", exc)
        return False


def notify_pending_alerts(db: Session) -> int:
    """Send Telegram messages for every unnotified alert; mark them is_notified=True.

    Dedup guarantee: alert rows already deduped at insert time by DB unique constraint
    (user_id, product_id, triggered_price).  Only alerts with is_notified=False are sent.

    Returns the number of successfully notified alerts.
    """
    cfg = get_settings()
    token = cfg.telegram_bot_token
    if not token:
        logger.debug("TELEGRAM_BOT_TOKEN not set; Telegram notifications skipped")
        return 0

    pending_alerts: list[Alert] = list(
        db.exec(select(Alert).where(Alert.is_notified == False)).all()  # noqa: E712
    )
    if not pending_alerts:
        return 0

    sent = 0
    for alert in pending_alerts:
        # Determine chat_id: prefer per-user, fall back to global config
        user = get_user_by_id(db, alert.user_id)
        chat_id = (
            user.telegram_chat_id if user and user.telegram_chat_id else ""
        ) or cfg.telegram_chat_id
        if not chat_id:
            logger.debug("No chat_id for user_id=%d; skipping", alert.user_id)
            continue

        product = get_product_by_id(db, alert.product_id)
        product_name = product.name if product else f"product#{alert.product_id}"

        text = _build_message(alert, product_name)
        ok = _send_telegram(token, chat_id, text)
        if ok:
            mark_notified(db, alert.id)  # type: ignore[arg-type]
            sent += 1

    logger.info("notify_pending_alerts: sent %d / %d pending", sent, len(pending_alerts))
    return sent
