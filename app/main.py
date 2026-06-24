"""PriceWatch FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.rate_limit import limiter
from app.jobs.scheduler import start_scheduler, stop_scheduler
from app.routers import admin, alerts, auth, health, products, users, watchlist


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = get_settings()
    configure_logging(cfg.log_level)
    start_scheduler()
    yield
    stop_scheduler()


def create_app() -> FastAPI:
    app = FastAPI(
        title="PriceWatch API",
        version="0.1.0",
        description="Sale price tracking with per-user watchlists and alerts.",
        lifespan=lifespan,
    )

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # Routers
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(products.router)
    app.include_router(watchlist.router)
    app.include_router(alerts.router)
    app.include_router(admin.router)

    return app


app = create_app()
