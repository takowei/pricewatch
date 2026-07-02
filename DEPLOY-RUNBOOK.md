# Deploy Runbook — pricewatch + pricedrop

Human-readable checklist for going from "brand-new Ubuntu box" to "both apps
live over HTTPS." Written for whoever has the server in front of them
(probably Root) — every step is one command.

> This is the combined runbook for **both** apps since they share one server
> and one reverse proxy. `pricedrop/DEPLOY-RUNBOOK.md` is a short pointer
> back to this file plus pricedrop-specific details.
>
> ⚠️ None of this has been run against a real server — `docker` is blocked in
> the dev sandbox that wrote it. Expect 1-2 rounds of debugging on the first
> real run. `bash -n` + shellcheck + `yaml.safe_load` all pass; that's the
> extent of what could be verified here.

---

## 0. What you need before you start

| Item                                                                  | Where it comes from                                                 |
| --------------------------------------------------------------------- | ------------------------------------------------------------------- |
| A fresh Ubuntu 22.04+ box, public IP, sudo access                     | Your friend                                                         |
| Two domains/subdomains (e.g. `watch.example.com`, `drop.example.com`) | Your DNS provider — point both **A records** at the box's public IP |
| GitHub repo secrets (below)                                           | You set these once in each repo's Settings → Secrets                |
| Real values for each app's `.env`                                     | See §3                                                              |

---

## 1. DNS

Point both subdomains at the server's public IP (A record). Do this **first**
— Caddy needs DNS to resolve before it can get a Let's Encrypt certificate.
Propagation is usually minutes, sometimes up to ~1 hour.

```
watch.example.com   A   <server public IP>
drop.example.com    A   <server public IP>
```

---

## 2. First-time server bootstrap

SSH into the box, then:

```bash
export PRICEWATCH_DOMAIN=watch.example.com
export PRICEDROP_DOMAIN=drop.example.com
curl -fsSL https://raw.githubusercontent.com/takowei/pricewatch/main/server_bootstrap.sh | bash
```

This installs Docker + bun, clones both repos into `~/apps/`, and — **on
this first run** — stops after writing placeholder `.env` files and tells
you to fill them in. That's expected. Continue to §3.

If it added you to the `docker` group for the first time, log out and back
in (or run `newgrp docker`) before re-running.

---

## 3. Fill in real secrets

### `~/apps/pricewatch/.env`

| Variable             | Required | Notes                                                                        |
| -------------------- | -------- | ---------------------------------------------------------------------------- |
| `POSTGRES_PASSWORD`  | **Yes**  | Strong, unique value                                                         |
| `JWT_SECRET`         | Yes      | `python3 -c "import secrets; print(secrets.token_hex(32))"`                  |
| `TELEGRAM_BOT_TOKEN` | No       | Leave blank to disable push alerts                                           |
| `TELEGRAM_CHAT_ID`   | No       | Required only if bot token is set                                            |
| `DATABASE_URL`       | No       | Leave as-is — docker-compose overrides it to point at the postgres container |

(Full reference: `docs/env.example.txt` in the pricewatch repo.)

### `~/apps/pricedrop/.env`

| Variable                | Required | Notes                                                                                                      |
| ----------------------- | -------- | ---------------------------------------------------------------------------------------------------------- |
| `LS_CHECKOUT_URL`       | Yes      | LemonSqueezy checkout link for your product (Products → your product → Checkout link)                      |
| `LEMON_WEBHOOK_SECRET`  | **Yes**  | LemonSqueezy → Settings → Webhooks → Signing secret. Without this, `/webhooks/lemon` rejects every request |
| `CRON_INTERVAL_SECONDS` | No       | Default `3600` (hourly price checks) — leave as-is                                                         |

(Full reference: `docs/env.example.txt` in the pricedrop repo.)

Edit both files, then re-run the bootstrap command from §2. This time it
will build both frontends, bring up both docker-compose stacks, start Caddy,
and run health checks.

---

## 4. GitHub Actions secrets (for auto-deploy on push to main)

Set these in **each repo separately** (Settings → Secrets and variables →
Actions → New repository secret). Same values in both repos if it's the
same server.

| Secret            | Value                                                                                                                             |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `DEPLOY_HOST`     | Server's public IP or hostname                                                                                                    |
| `DEPLOY_USER`     | SSH username (the sudo-capable user from §2)                                                                                      |
| `DEPLOY_SSH_KEY`  | Private key (PEM, no passphrase) that can SSH into the box. Add the matching public key to `~/.ssh/authorized_keys` on the server |
| `DEPLOY_SSH_PORT` | Optional — only if not port 22                                                                                                    |

Until these are set, `.github/workflows/deploy.yml` runs but **skips** the
actual deploy step (safe no-op) — see the `secrets_check` step in each
workflow.

Once set: every push to `main` (after CI passes) pulls the latest code,
rebuilds, restarts, and rebuilds the frontend on the server.

---

## 5. Acceptance checklist

Run each of these after step 2/3 completes (or after a GitHub Actions deploy):

```bash
# 1. Both containers are up
docker ps --format '{{.Names}}\t{{.Status}}'
#   expect: pricewatch-app, pricewatch-postgres, pricedrop-app, pricedrop-cron, edge-caddy — all "Up"

# 2. Direct health checks (bypass Caddy — confirms the app itself is fine)
curl -s http://localhost:8000/health   # pricewatch -> {"status":"ok"}
curl -s http://localhost:8001/health   # pricedrop  -> {"status":"ok"}

# 3. HTTPS via Caddy (confirms DNS + TLS cert issuance worked)
curl -s https://watch.example.com/health
curl -s https://drop.example.com/health

# 4. Frontend loads
curl -sI https://watch.example.com/ | head -1   # expect: HTTP/2 200
curl -sI https://drop.example.com/  | head -1   # expect: HTTP/2 200

# 5. pricedrop's hourly cron is actually running
docker compose -f ~/apps/pricedrop/docker-compose.yml logs cron --tail=20
#   expect a "[cron_loop] ... running check_prices..." line

# 6. LemonSqueezy webhook reachable (once LEMON_WEBHOOK_SECRET is set)
curl -s -o /dev/null -w '%{http_code}\n' https://drop.example.com/webhooks/lemon
#   expect 400 (bad signature) — NOT 404/502. 400 means routing + app are alive;
#   the real webhook test happens by triggering a test event from the LS dashboard.
```

---

## 6. Updating later

Just `git push` to `main` on either repo — GitHub Actions (§4) handles the
rest. To update manually instead:

```bash
cd ~/apps/pricewatch && git pull && docker compose up -d --build
cd ~/apps/pricedrop  && git pull && docker compose up -d --build
```

---

## 7. Known limitations (honest, not swept under the rug)

- **Not tested end-to-end.** Every file here passed static checks
  (`bash -n`, shellcheck, YAML/Python syntax validation, `pytest`) but never
  ran against real Docker or a real server. Budget time for a first-run
  debugging pass.
- **pricedrop uses SQLite**, shared between the `app` and `cron` containers
  via one Docker volume. SQLite handles this fine at pricedrop's current
  scale (low write volume, one writer at a time in practice), but if traffic
  grows, migrate to Postgres the same way pricewatch already does.
- **pricewatch's scheduler runs in-process** (APScheduler, single uvicorn
  worker) — this is existing app behavior, not something this deploy layer
  changes. Don't scale pricewatch's `app` service beyond 1 replica or the
  daily scrape job will fire multiple times (see `app/jobs/scheduler.py`
  docstring).
- **CORS** in pricedrop's `app/main.py` still hardcodes
  `http://localhost:5173` as the only allowed origin. Harmless in this
  same-origin-via-Caddy design (frontend and API share one domain, so the
  browser never sends a cross-origin request in production) — flagged here
  in case that assumption ever changes.
- **Caddy TLS** needs port 80 AND 443 reachable from the internet for
  Let's Encrypt's HTTP-01 challenge. If your server is behind another
  firewall/NAT, open both ports first.
