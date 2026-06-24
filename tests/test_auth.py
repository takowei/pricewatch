"""Auth endpoint tests: register, login, refresh, token expiry/tampering."""

from __future__ import annotations

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.security import create_token, decode_token, hash_password, verify_password
from tests.factories import make_user

# ── Unit: password hashing ────────────────────────────────────────────────────


def test_hash_and_verify_password():
    h = hash_password("secret123")
    assert verify_password("secret123", h)
    assert not verify_password("wrong", h)


def test_verify_password_wrong_returns_false():
    h = hash_password("correct")
    assert not verify_password("incorrect", h)


# ── Unit: JWT ─────────────────────────────────────────────────────────────────


def test_create_and_decode_access_token():
    token = create_token("42", "access")
    assert decode_token(token, "access") == "42"


def test_create_and_decode_refresh_token():
    token = create_token("7", "refresh")
    assert decode_token(token, "refresh") == "7"


def test_wrong_token_type_rejected():
    access = create_token("1", "access")
    with pytest.raises(jwt.InvalidTokenError):
        decode_token(access, "refresh")


def test_tampered_token_rejected():
    token = create_token("1", "access")
    tampered = token[:-4] + "xxxx"
    with pytest.raises(jwt.InvalidTokenError):
        decode_token(tampered, "access")


# ── Integration: auth endpoints ───────────────────────────────────────────────


def test_register_returns_tokens(client: TestClient):
    resp = client.post("/auth/register", json={"email": "a@b.com", "password": "pass1234"})
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_email_409(client: TestClient):
    payload = {"email": "dup@b.com", "password": "pass1234"}
    client.post("/auth/register", json=payload)
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 409


def test_register_short_password_422(client: TestClient):
    resp = client.post("/auth/register", json={"email": "x@b.com", "password": "short"})
    assert resp.status_code == 422


def test_login_success(client: TestClient, db):
    make_user(db, email="login@b.com", password="mypassword")
    resp = client.post("/auth/login", json={"email": "login@b.com", "password": "mypassword"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password_401(client: TestClient, db):
    make_user(db, email="x@b.com", password="correct")
    resp = client.post("/auth/login", json={"email": "x@b.com", "password": "wrong"})
    assert resp.status_code == 401


def test_login_unknown_email_401(client: TestClient):
    resp = client.post("/auth/login", json={"email": "ghost@b.com", "password": "pass"})
    assert resp.status_code == 401


def test_bearer_token_grants_access_to_me(client: TestClient, db):
    make_user(db, email="me@b.com", password="pass1234")
    login = client.post("/auth/login", json={"email": "me@b.com", "password": "pass1234"})
    token = login.json()["access_token"]
    resp = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@b.com"


def test_missing_token_401(client: TestClient):
    resp = client.get("/users/me")
    # FastAPI's HTTPBearer(auto_error=True) returns 403 in older versions, 401 in newer
    assert resp.status_code in (401, 403)


def test_tampered_bearer_401(client: TestClient):
    resp = client.get(
        "/users/me",
        headers={"Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.fake.sig"},
    )
    assert resp.status_code == 401


def test_refresh_issues_new_access_token(client: TestClient, db):
    make_user(db, email="r@b.com", password="pass1234")
    login = client.post("/auth/login", json={"email": "r@b.com", "password": "pass1234"})
    refresh_token = login.json()["refresh_token"]
    resp = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_access_token_used_as_refresh_rejected(client: TestClient, db):
    make_user(db, email="r2@b.com", password="pass1234")
    login = client.post("/auth/login", json={"email": "r2@b.com", "password": "pass1234"})
    access_token = login.json()["access_token"]
    resp = client.post("/auth/refresh", json={"refresh_token": access_token})
    assert resp.status_code == 401


def test_expired_token_rejected():
    """Create a token with exp in the past; decode must raise ExpiredSignatureError."""
    from datetime import datetime, timedelta, timezone

    from app.core.config import get_settings

    cfg = get_settings()
    # Manually issue an already-expired token (exp = 2 seconds ago)
    payload = {
        "sub": "99",
        "type": "access",
        "exp": datetime.now(tz=timezone.utc) - timedelta(seconds=2),
        "iat": datetime.now(tz=timezone.utc) - timedelta(seconds=10),
        "jti": "test",
    }
    import jwt as _jwt

    token = _jwt.encode(payload, cfg.jwt_secret, algorithm=cfg.jwt_algorithm)
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(token, "access")
