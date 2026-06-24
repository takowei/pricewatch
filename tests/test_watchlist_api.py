"""Watchlist API integration tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_token
from tests.factories import make_user


def _auth_header_for_user(user_id: int) -> dict:
    """Build Bearer header directly from user_id (avoids rate-limit on /auth/login)."""
    token = create_token(str(user_id), "access")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def auth(client: TestClient, db):
    user = make_user(db, email="u@b.com", password="pass1234")
    return _auth_header_for_user(user.id)


def test_list_watchlist_empty(client: TestClient, auth):
    resp = client.get("/watchlist", headers=auth)
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_watchlist_item(client: TestClient, auth):
    resp = client.post(
        "/watchlist",
        json={"keyword": "束口褲", "max_price": 800},
        headers=auth,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["keyword"] == "束口褲"
    assert data["max_price"] == 800
    assert data["is_active"] is True


def test_list_after_create(client: TestClient, auth):
    client.post("/watchlist", json={"keyword": "T-shirt"}, headers=auth)
    resp = client.get("/watchlist", headers=auth)
    assert len(resp.json()) == 1


def test_update_watchlist_item(client: TestClient, auth):
    create = client.post("/watchlist", json={"keyword": "Pants", "max_price": 1000}, headers=auth)
    item_id = create.json()["id"]
    resp = client.patch(f"/watchlist/{item_id}", json={"max_price": 500}, headers=auth)
    assert resp.status_code == 200
    assert resp.json()["max_price"] == 500


def test_delete_watchlist_item(client: TestClient, auth):
    create = client.post("/watchlist", json={"keyword": "Jacket"}, headers=auth)
    item_id = create.json()["id"]
    resp = client.delete(f"/watchlist/{item_id}", headers=auth)
    assert resp.status_code == 204
    assert client.get("/watchlist", headers=auth).json() == []


def test_cannot_access_other_users_watchlist(client: TestClient, db):
    other = make_user(db, email="other@b.com", password="pass1234")
    owner = make_user(db, email="owner@b.com", password="pass1234")

    auth_other = _auth_header_for_user(other.id)
    auth_owner = _auth_header_for_user(owner.id)

    create = client.post("/watchlist", json={"keyword": "Secret"}, headers=auth_owner)
    item_id = create.json()["id"]

    resp = client.patch(f"/watchlist/{item_id}", json={"keyword": "Stolen"}, headers=auth_other)
    assert resp.status_code == 404

    resp = client.delete(f"/watchlist/{item_id}", headers=auth_other)
    assert resp.status_code == 404


def test_watchlist_requires_auth(client: TestClient):
    # HTTPBearer returns 401 or 403 depending on FastAPI version
    assert client.get("/watchlist").status_code in (401, 403)
