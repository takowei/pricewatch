"""API docs (Swagger/ReDoc/OpenAPI schema) must be off by default, since this
API is intended to be reachable over a public tunnel — the schema would hand
an anonymous internet caller a full map of every route.
"""

from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def prod_app(monkeypatch: pytest.MonkeyPatch):
    """Reimport app.main with ENABLE_DOCS unset (production default)."""
    monkeypatch.delenv("ENABLE_DOCS", raising=False)

    import app.core.config as config_module
    import app.main as main_module

    config_module._settings = None
    importlib.reload(main_module)
    yield main_module.app

    config_module._settings = None
    importlib.reload(main_module)


@pytest.fixture()
def dev_app(monkeypatch: pytest.MonkeyPatch):
    """Reimport app.main with ENABLE_DOCS=1 (opt-in for local dev)."""
    monkeypatch.setenv("ENABLE_DOCS", "1")

    import app.core.config as config_module
    import app.main as main_module

    config_module._settings = None
    importlib.reload(main_module)
    yield main_module.app

    config_module._settings = None
    importlib.reload(main_module)


class TestDocsDisabledByDefault:
    def test_docs_route_returns_404(self, prod_app):
        with TestClient(prod_app) as client:
            r = client.get("/docs")
        assert r.status_code == 404

    def test_redoc_route_returns_404(self, prod_app):
        with TestClient(prod_app) as client:
            r = client.get("/redoc")
        assert r.status_code == 404

    def test_openapi_json_returns_404(self, prod_app):
        with TestClient(prod_app) as client:
            r = client.get("/openapi.json")
        assert r.status_code == 404

    def test_health_still_works(self, prod_app):
        """Disabling docs must not affect normal routes."""
        with TestClient(prod_app) as client:
            r = client.get("/health")
        assert r.status_code == 200


class TestDocsEnabledViaEnvVar:
    def test_docs_route_available_when_opted_in(self, dev_app):
        with TestClient(dev_app) as client:
            r = client.get("/docs")
        assert r.status_code == 200

    def test_openapi_json_available_when_opted_in(self, dev_app):
        with TestClient(dev_app) as client:
            r = client.get("/openapi.json")
        assert r.status_code == 200
