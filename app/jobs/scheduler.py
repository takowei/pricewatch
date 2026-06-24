"""APScheduler setup.

Usage: call start_scheduler() inside FastAPI lifespan, stop_scheduler() on shutdown.

Multi-worker warning:
  uvicorn --workers N creates N processes each running their own scheduler instance,
  causing the job to fire N times simultaneously. Mitigations:
    1. Run uvicorn with a single worker (recommended for this app's scale).
    2. Set SCHEDULER_ENABLED=false on all but one worker via an env toggle.
  This is documented in README.md.
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.jobs.tasks import scrape_all

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None

# Daily at 02:00 UTC by default — change via SCHEDULER_CRON_HOUR env if needed.
_CRON_HOUR = 2
_CRON_MINUTE = 0


def start_scheduler() -> None:
    """Create and start the background scheduler. Safe to call multiple times."""
    global _scheduler  # noqa: PLW0603
    if _scheduler is not None and _scheduler.running:
        logger.debug("scheduler already running; skipping start")
        return

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        scrape_all,
        trigger=CronTrigger(hour=_CRON_HOUR, minute=_CRON_MINUTE, timezone="UTC"),
        id="scrape_all",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    _scheduler.start()
    logger.info("scheduler started (daily %02d:%02d UTC)", _CRON_HOUR, _CRON_MINUTE)


def stop_scheduler() -> None:
    """Gracefully shut down the scheduler on app teardown."""
    global _scheduler  # noqa: PLW0603
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("scheduler stopped")
    _scheduler = None
