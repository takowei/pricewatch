"""CORS must allow-list exact frontend origins, never "*".

The frontend is deployed as a separately-hosted SPA (different origin from
the API), so the browser needs an explicit CORS allow-list to let it call
the API at all. This is configured via the CORS_ORIGINS env var.
"""

from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def app_with_origin(monkeypatch: pytest.MonkeyPatch):
    """Reimport app.main with CORS_ORIGINS set to a single custom origin."""
    monkeypatch.setenv("CORS_ORIGINS", "https://frontend.example.com")

    import app.core.config as config_module
    import app.main as main_module

    config_module._settings = None
    importlib.reload(main_module)
    yield main_module.app

    config_module._settings = None
    importlib.reload(main_module)


class TestCorsAllowList:
    def test_allowed_origin_gets_cors_header(self, app_with_origin):
        with TestClient(app_with_origin) as client:
            resp = client.get("/health", headers={"Origin": "https://frontend.example.com"})
        assert resp.headers["access-control-allow-origin"] == "https://frontend.example.com"

    def test_other_origin_gets_no_cors_header(self, app_with_origin):
        with TestClient(app_with_origin) as client:
            resp = client.get("/health", headers={"Origin": "https://evil.example.com"})
        assert "access-control-allow-origin" not in resp.headers

    def test_never_wildcard(self, app_with_origin):
        with TestClient(app_with_origin) as client:
            resp = client.get("/health", headers={"Origin": "https://frontend.example.com"})
        assert resp.headers["access-control-allow-origin"] != "*"
