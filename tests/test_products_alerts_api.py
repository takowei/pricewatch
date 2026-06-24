"""Integration tests for GET /products and GET /alerts endpoints (Phase 0-4 gap)."""

from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient

from app.core.security import create_token
from tests.factories import make_price_history, make_product, make_user, make_watchlist


def _auth(user_id: int) -> dict:
    token = create_token(str(user_id), "access")
    return {"Authorization": f"Bearer {token}"}


# ── GET /products ─────────────────────────────────────────────────────────────


def test_list_products_empty(client: TestClient):
    resp = client.get("/products")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_products_returns_inserted(client: TestClient, db):
    make_product(db, name="Slim Fit Pants", brand="uniqlo")
    make_product(db, name="Wide Chino", brand="net", product_url="https://example.com/2")

    resp = client.get("/products")
    assert resp.status_code == 200
    names = [p["name"] for p in resp.json()]
    assert "Slim Fit Pants" in names
    assert "Wide Chino" in names


def test_list_products_filter_brand(client: TestClient, db):
    make_product(db, brand="uniqlo", product_url="https://example.com/u1")
    make_product(db, brand="net", name="NET Shirt", product_url="https://example.com/n1")

    resp = client.get("/products", params={"brand": "net"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["brand"] == "net"


def test_list_products_filter_keyword(client: TestClient, db):
    make_product(db, name="Jogger Pants", product_url="https://example.com/j1")
    make_product(db, name="Plain T-Shirt", product_url="https://example.com/t1")

    resp = client.get("/products", params={"keyword": "jogger"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert "Jogger" in data[0]["name"]


def test_get_product_by_id(client: TestClient, db):
    p = make_product(db, name="Cargo Pants", product_url="https://example.com/cargo")
    resp = client.get(f"/products/{p.id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Cargo Pants"


def test_get_product_not_found(client: TestClient):
    resp = client.get("/products/99999")
    assert resp.status_code == 404


def test_get_product_history(client: TestClient, db):
    p = make_product(db, product_url="https://example.com/hist")
    make_price_history(db, product_id=p.id, sale_price=590, recorded_date=date(2026, 6, 1))
    make_price_history(db, product_id=p.id, sale_price=490, recorded_date=date(2026, 6, 2))

    resp = client.get(f"/products/{p.id}/history")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["sale_price"] == 590
    assert data[1]["sale_price"] == 490


# ── GET /alerts ───────────────────────────────────────────────────────────────


def test_list_alerts_requires_auth(client: TestClient):
    assert client.get("/alerts").status_code in (401, 403)


def test_list_alerts_empty_for_new_user(client: TestClient, db):
    user = make_user(db, email="noalert@b.com")
    resp = client.get("/alerts", headers=_auth(user.id))
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_alerts_returns_own_alerts(client: TestClient, db):
    from app.repositories.alert_repo import create_alert_if_new

    user = make_user(db, email="alertuser@b.com")
    wl = make_watchlist(db, user_id=user.id, keyword="Pants")
    product = make_product(db, product_url="https://example.com/alert-p")

    create_alert_if_new(
        db,
        user_id=user.id,
        watchlist_id=wl.id,
        product_id=product.id,
        triggered_price=590,
        reason="at_target",
    )

    resp = client.get("/alerts", headers=_auth(user.id))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["triggered_price"] == 590
    assert data[0]["reason"] == "at_target"


def test_alerts_not_visible_to_other_user(client: TestClient, db):
    from app.repositories.alert_repo import create_alert_if_new

    owner = make_user(db, email="owner@b.com")
    other = make_user(db, email="other@b.com")
    wl = make_watchlist(db, user_id=owner.id, keyword="Pants")
    product = make_product(db, product_url="https://example.com/iso-p")

    create_alert_if_new(
        db,
        user_id=owner.id,
        watchlist_id=wl.id,
        product_id=product.id,
        triggered_price=590,
        reason="at_target",
    )

    resp = client.get("/alerts", headers=_auth(other.id))
    assert resp.status_code == 200
    assert resp.json() == []
