# PriceWatch — Deployment Guide

> 📌 **The old AWS box this script targeted is no longer reachable.** For
> deploying to a new server (any Ubuntu host, provisioned generically — not
> AWS-specific), use `server_bootstrap.sh` + `../DEPLOY-RUNBOOK.md` at the
> repo root instead. This document and `deploy_aws.sh` are kept for
> reference / in case an AWS-style single-repo deploy is useful again.

> ⚠️ `deploy_aws.sh` was written by the dev-lead agent but **cannot be tested in the sandbox**
> (Docker is blocked, and the AWS box is unreachable from the agent).
> Expect 1–2 rounds of debugging when you run it for the first time.

---

## Quick Start

```bash
# 1. Set secrets in your local shell (never commit these)
export POSTGRES_PASSWORD='your-strong-password'
export TELEGRAM_BOT_TOKEN='123456:ABC...'   # optional
export TELEGRAM_CHAT_ID='your_chat_id'      # optional
# JWT_SECRET is auto-generated if not set

# 2. Run the deploy script from the repo root
bash deploy_aws.sh
```

That's it. The script handles everything from step 3 onwards.

---

## Prerequisites

### Local machine (your WSL terminal)

| Tool                  | Version | Notes                                                                       |
| --------------------- | ------- | --------------------------------------------------------------------------- |
| bash                  | any     | ships with WSL                                                              |
| ssh + scp             | any     | ships with WSL                                                              |
| openssl               | any     | for JWT_SECRET generation (fallback: set manually)                          |
| `sol-grid-trader.pem` | —       | same key as the trading box; must be in repo root or `SSH_KEY=/path/to/key` |

### Remote box (57.182.243.118 — Ubuntu)

Install once, then the script handles the rest:

```bash
# Docker CE + compose V2 plugin
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker ubuntu    # allow ubuntu user to run docker without sudo
# then log out and back in, or: newgrp docker
```

### AWS Security Group

Open inbound TCP **8000** (or your `APP_PORT`) from `0.0.0.0/0` (or restrict to your IP).
Port 5432 (postgres) does **not** need to be public — it's container-internal only.

---

## Environment Variables

| Variable                      | Required | Default               | Description                                                      |
| ----------------------------- | -------- | --------------------- | ---------------------------------------------------------------- |
| `POSTGRES_PASSWORD`           | Yes      | —                     | PostgreSQL password; set strong, unique value                    |
| `JWT_SECRET`                  | No       | auto-generated        | 64-char hex; auto-generated with `openssl rand -hex 32` if unset |
| `JWT_ALGORITHM`               | No       | `HS256`               | JWT signing algorithm                                            |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No       | `30`                  | Access token lifetime                                            |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | No       | `7`                   | Refresh token lifetime                                           |
| `TELEGRAM_BOT_TOKEN`          | No       | `` (empty)            | Leave blank to disable push alerts                               |
| `TELEGRAM_CHAT_ID`            | No       | `` (empty)            | Required if bot token is set                                     |
| `APP_ENV`                     | No       | `production`          | App environment tag                                              |
| `LOG_LEVEL`                   | No       | `INFO`                | Uvicorn + app log level                                          |
| `SSH_KEY`                     | No       | `sol-grid-trader.pem` | Path to SSH private key                                          |
| `APP_PORT`                    | No       | `8000`                | Host port to expose                                              |

All secrets flow: **local shell env → remote `.env` (chmod 600) → container**.
The `.env` file is gitignored and never printed by the script.

---

## What the Script Does (Step by Step)

| Step | Action                                                                                  |
| ---- | --------------------------------------------------------------------------------------- |
| 1    | SSH connectivity check                                                                  |
| 2    | Pack repo into a tarball (excludes `.git`, `.env`, caches, tests)                       |
| 3    | `scp` tarball to box → unpack under `/home/ubuntu/pricewatch/`                          |
| 4    | Write `.env` on the box via stdin pipe (secrets never touch a local file)               |
| 5    | Verify Docker CE + compose V2 are installed                                             |
| 6    | `docker compose up -d --build` → wait for postgres healthcheck → `alembic upgrade head` |
| 7    | `curl /health` → print access URLs                                                      |

Re-running the script is **idempotent**: existing containers are replaced with the new build,
and the `pgdata` volume is preserved (your data survives).

---

## After Deployment

```
Live app  : http://57.182.243.118:8000
Swagger UI: http://57.182.243.118:8000/docs
```

### Useful box commands

```bash
# ssh in
ssh -i sol-grid-trader.pem ubuntu@57.182.243.118

# on the box:
cd /home/ubuntu/pricewatch

docker compose logs -f app          # tail app logs
docker compose logs -f postgres     # tail DB logs
docker compose restart app          # restart only the app (keep DB running)
docker compose down                 # stop everything (pgdata volume kept)
docker compose down -v              # ⚠️ also deletes pgdata — data loss!
docker compose exec app alembic upgrade head   # run migrations manually
```

### Updating the app

Just re-run `deploy_aws.sh` from your local machine — it repacks, ships, and restarts.

---

## Troubleshooting

**`/health` returns non-200 immediately after deploy**
The app container may still be initialising. Wait 10–20 s and retry:

```bash
ssh -i sol-grid-trader.pem ubuntu@57.182.243.118 \
  "curl -s http://localhost:8000/health"
```

**postgres healthcheck never passes**
Check postgres logs: `docker compose logs postgres --tail=30`
Common cause: wrong `POSTGRES_PASSWORD` in `.env`.

**`alembic upgrade head` fails**
Usually a `DATABASE_URL` mismatch. Verify `.env` on the box:

```bash
grep DATABASE_URL /home/ubuntu/pricewatch/.env
```

**Port 8000 unreachable from browser**
Check AWS Security Group inbound rules — TCP 8000 must be open.

**"docker: permission denied"**
The `ubuntu` user is not yet in the `docker` group.
Run `sudo usermod -aG docker ubuntu` then log out and back in (or `newgrp docker`).
