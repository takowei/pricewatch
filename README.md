# PriceWatch

> Multi-user price-alert SaaS backend — track product prices, get notified the moment a watched item hits your target or drops.

PriceWatch began as a personal sale-scraping script ([sale-tracker](https://github.com/takowei/sale-tracker), which scraped 363 live products with working Telegram alerts) and was rewritten into a **multi-user service built to a ship-to-production standard**: layered architecture, real authentication, background scheduling, containerization, and CI.

**Stack:** Python · FastAPI · SQLModel · PostgreSQL · Alembic · JWT (argon2) · APScheduler · Docker · React + TypeScript + Vite

**Status:** 🟢 Full stack complete (backend + frontend), containerized, CI green — pending deployment for a public live-demo URL.

---

## What it does

1. Scrapers (UNIQLO official API, NET static parsing) pull product prices on a daily schedule.
2. Each price is ingested and appended to a price history.
3. A detection pass compares every user's **watchlist** (keyword + target price) against the latest prices.
4. When an item hits target or drops, the user is notified via Telegram — **deduplicated** so the same alert never fires twice.
5. A React SPA lets users register/login, browse & filter products, view price-trend charts, and manage their watchlist and alerts.

---

## Architecture

Clean three-layer separation, dependencies pointing inward:

```
HTTP ─▶ routers/ ──▶ services/ ──▶ repositories/ ──▶ db (PostgreSQL)
            │            │
        schemas/      core/ (security, config, rate-limit, logging)
                         │
                  scrapers/  jobs/ (APScheduler)
```

- **routers/** — FastAPI endpoints (auth, products, watchlist, alerts). Thin; no business logic.
- **services/** — business logic. Price-target / price-drop detection is written as **pure functions** for easy, deterministic testing.
- **repositories/** — all DB access; the rest of the app never touches the session directly.
- **core/** — JWT, password hashing, settings, rate limiting, structured logging.
- **models/ · schemas/** — SQLModel tables vs. Pydantic request/response models (kept separate).
- **scrapers/ · jobs/** — data acquisition and the APScheduler daily pipeline.

## Engineering highlights

- **Authentication (hand-rolled, not a library shortcut):** JWT **access / refresh split** distinguished by a `type` claim and per-token `jti`; **argon2id** password hashing with constant-time verification; all secrets via environment variables.
- **Idempotent alerts:** detection is a pure function over (watchlist × latest prices); duplicate notifications are prevented by a **database unique constraint**, not ad-hoc checks.
- **Rate limiting & structured logging** in the core layer (slowapi).
- **Background pipeline:** scrape → ingest → detect → notify runs fully automated via APScheduler (started in the FastAPI lifespan, not at import time).
- **Containerization:** multi-stage Dockerfile (non-root user + healthcheck) and `docker-compose` (app + postgres).
- **Frontend:** Vite + React + TypeScript SPA — login, product list with filter/sort, price-trend charts (Recharts), watchlist CRUD, alerts page. Centralized API client with **automatic 401 → refresh-token retry** (guarded against infinite loops).

## Testing & CI

- **60 backend tests** (pytest): pure detection logic, auth, API integration, and notifications — HTTP and DB are fully mocked so the suite runs **offline**.
- **GitHub Actions CI:** `ruff` (format + lint) + `pytest` on every push.
- **Frontend:** passes `tsc` (type-check), `oxlint`, and `vite build`.

---

## Running locally

```bash
# 1. Configure environment (see docs/env.example.txt)
cp docs/env.example.txt .env        # then fill in secrets

# 2. Start app + PostgreSQL
docker compose up --build

# API:        http://localhost:8000
# OpenAPI UI: http://localhost:8000/docs
```

Frontend:

```bash
cd frontend
bun install
bun run dev
```

Tests:

```bash
pip install -e ".[dev]"
pytest
```

Deployment notes (AWS / single-host docker-compose) are in [`docs/DEPLOY.md`](docs/DEPLOY.md); the full design rationale is in [`docs/BLUEPRINT.md`](docs/BLUEPRINT.md).

---

## Project layout

```
app/
  routers/        # FastAPI endpoints
  services/       # business logic (pure-function detection)
  repositories/   # DB access
  core/           # security, config, rate-limit, logging
  models/         # SQLModel tables
  schemas/        # Pydantic request/response models
  scrapers/       # UNIQLO / NET scrapers
  jobs/           # APScheduler daily pipeline
  db/             # engine / session
  main.py         # app factory + lifespan
alembic/          # migrations
frontend/         # Vite + React + TypeScript SPA
tests/            # 60 pytest tests (offline, mocked)
Dockerfile · docker-compose.yml · .github/ (CI)
```

## Status & honesty note

Backend (Phases 0–7) and frontend are complete; the image builds, CI is green, and the test suite passes offline. The one thing not yet done is a **public deployment** — so there is no live-demo URL yet. Nothing here is marked "done" that hasn't been verified, and the repo contains no secrets or private data.
