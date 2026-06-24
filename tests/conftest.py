"""Test fixtures.

Strategy:
- StaticPool + SQLite in-memory: forces all connections to reuse the same
  underlying connection, so data written in one Session is visible to another
  within the same test (critical for client + db fixture sharing).
- Each test gets its own engine (fresh create_all) → full isolation.
- FastAPI's get_db dependency is overridden per-test via app.dependency_overrides.
"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

# Must be set before any app import
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-do-not-use-in-prod")

import app.models  # noqa: F401, E402 — registers all tables in SQLModel.metadata
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def engine():
    """Fresh SQLite engine per test with StaticPool so all sessions share one connection."""
    _engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(_engine)
    yield _engine
    SQLModel.metadata.drop_all(_engine)
    _engine.dispose()


@pytest.fixture()
def db(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture()
def client(engine):
    def _get_test_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)
