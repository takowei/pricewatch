"""Database session factory (synchronous, psycopg3 / SQLite for tests)."""

from __future__ import annotations

from collections.abc import Generator

from sqlmodel import Session, create_engine

from app.core.config import get_settings

_engine = None


def get_engine():
    global _engine  # noqa: PLW0603
    if _engine is None:
        cfg = get_settings()
        connect_args: dict = {}
        if cfg.database_url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
        _engine = create_engine(
            cfg.database_url,
            connect_args=connect_args,
            echo=False,
        )
    return _engine


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yield a Session, always closed after request."""
    engine = get_engine()
    with Session(engine) as session:
        yield session
