#!/usr/bin/env bash
# server_bootstrap.sh — bring up pricewatch + pricedrop on a brand-new Ubuntu box.
#
# This is the CANONICAL copy. pricedrop/server_bootstrap.sh is a thin wrapper
# that fetches and execs this file, so there is only one copy to maintain.
# It bootstraps BOTH apps regardless of which repo you happened to clone
# first, because they share one server + one reverse proxy.
#
# ⚠️  NOT TESTED END-TO-END — the dev sandbox that wrote this script has
#     docker blocked, so this has only been syntax- and lint-checked
#     (bash -n + static analysis). Expect to debug on first real run
#     (see docs/DEPLOY.md / DEPLOY-RUNBOOK.md for troubleshooting).
#
# Usage (on the fresh Ubuntu box, as a sudo-capable non-root user):
#
#     export PRICEWATCH_DOMAIN=watch.example.com
#     export PRICEDROP_DOMAIN=drop.example.com
#     curl -fsSL https://raw.githubusercontent.com/takowei/pricewatch/main/server_bootstrap.sh | bash
#     # or, if you already cloned a repo:
#     bash server_bootstrap.sh
#
# Safe to re-run any time — every step is idempotent (checks before acting).
# On first run without real .env files, the script stops after writing
# docs/env.example.txt -> .env so you can fill in real secrets, then re-run.
#
# shellcheck disable=SC2129,SC1091,SC2016

set -euo pipefail

# ── Config (override via env vars) ────────────────────────────────────────────
APPS_DIR="${APPS_DIR:-$HOME/apps}"
PRICEWATCH_REPO="${PRICEWATCH_REPO:-https://github.com/takowei/pricewatch.git}"
PRICEDROP_REPO="${PRICEDROP_REPO:-https://github.com/takowei/pricedrop.git}"
PRICEWATCH_DOMAIN="${PRICEWATCH_DOMAIN:-pricewatch.example.com}"
PRICEDROP_DOMAIN="${PRICEDROP_DOMAIN:-pricedrop.example.com}"
CADDY_ACME_EMAIL="${CADDY_ACME_EMAIL:-}"
EDGE_NETWORK="edge"

log() { echo "[bootstrap] $*"; }
warn() { echo "[bootstrap] WARNING: $*" >&2; }
die() {
    echo "[bootstrap] ERROR: $*" >&2
    exit 1
}

# ── 1. Docker CE + compose plugin ─────────────────────────────────────────────
install_docker() {
    if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
        log "docker + compose plugin already installed, skipping."
        return
    fi
    log "installing Docker CE + compose plugin..."
    sudo apt-get update
    sudo apt-get install -y ca-certificates curl gnupg
    sudo install -m 0755 -d /etc/apt/keyrings
    if [ ! -f /etc/apt/keyrings/docker.gpg ]; then
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg |
            sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    fi
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" |
        sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    if ! groups "$USER" | grep -q docker; then
        sudo usermod -aG docker "$USER"
        warn "added $USER to the docker group — log out and back in (or run: newgrp docker) before re-running this script."
        exit 0
    fi
}

# ── 2. bun (for building both frontends) ──────────────────────────────────────
install_bun() {
    if command -v bun >/dev/null 2>&1; then
        log "bun already installed ($(bun --version)), skipping."
        return
    fi
    log "installing bun..."
    curl -fsSL https://bun.sh/install | bash
    export PATH="$HOME/.bun/bin:$PATH"
    if ! grep -q '.bun/bin' "$HOME/.bashrc" 2>/dev/null; then
        echo 'export PATH="$HOME/.bun/bin:$PATH"' >>"$HOME/.bashrc"
    fi
}

# ── 3. Shared reverse-proxy docker network ────────────────────────────────────
ensure_edge_network() {
    if docker network inspect "$EDGE_NETWORK" >/dev/null 2>&1; then
        log "docker network '$EDGE_NETWORK' already exists, skipping."
    else
        log "creating docker network '$EDGE_NETWORK'..."
        docker network create "$EDGE_NETWORK"
    fi
}

# ── 4. Clone or update a repo ──────────────────────────────────────────────────
sync_repo() {
    local repo_url="$1" dir="$2"
    if [ -d "$dir/.git" ]; then
        log "updating $dir..."
        git -C "$dir" fetch origin main
        git -C "$dir" reset --hard origin/main
    else
        log "cloning $repo_url -> $dir..."
        mkdir -p "$(dirname "$dir")"
        git clone "$repo_url" "$dir"
    fi
}

# ── 5. Ensure .env exists (stop for the human to fill secrets on first run) ──
ensure_env_file() {
    local dir="$1" example="$2"
    if [ -f "$dir/.env" ]; then
        return 0
    fi
    if [ ! -f "$dir/$example" ]; then
        die "$dir/$example not found — can't seed .env."
    fi
    cp "$dir/$example" "$dir/.env"
    warn "wrote $dir/.env from $example with PLACEHOLDER values."
    warn "  -> edit $dir/.env with real secrets, then re-run this script."
    return 1
}

# ── 6. Build a frontend (bun install + build) ─────────────────────────────────
build_frontend() {
    local dir="$1" api_base="${2:-}"
    log "building frontend in $dir (VITE_API_BASE_URL='$api_base')..."
    (cd "$dir" && bun install --frozen-lockfile && VITE_API_BASE_URL="$api_base" bun run build)
}

# ── 7. docker compose up for one app ──────────────────────────────────────────
compose_up() {
    local dir="$1"
    log "docker compose up -d --build in $dir..."
    (cd "$dir" && docker compose up -d --build)
}

# ── 8. Write the merged Caddyfile + bring up the shared reverse proxy ────────
setup_caddy() {
    local caddy_dir="$APPS_DIR/caddy"
    mkdir -p "$caddy_dir"

    log "writing $caddy_dir/Caddyfile..."
    {
        if [ -n "$CADDY_ACME_EMAIL" ]; then
            echo "{"
            echo "    email $CADDY_ACME_EMAIL"
            echo "}"
            echo
        fi
        sed "s/PRICEWATCH_DOMAIN/$PRICEWATCH_DOMAIN/" "$APPS_DIR/pricewatch/deploy/Caddyfile.fragment"
        echo
        sed "s/PRICEDROP_DOMAIN/$PRICEDROP_DOMAIN/" "$APPS_DIR/pricedrop/deploy/Caddyfile.fragment"
    } >"$caddy_dir/Caddyfile"

    cat >"$caddy_dir/docker-compose.yml" <<EOF
services:
  caddy:
    image: caddy:2-alpine
    container_name: edge-caddy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - $APPS_DIR/pricewatch/frontend/dist:/srv/pricewatch:ro
      - $APPS_DIR/pricedrop/frontend/dist:/srv/pricedrop:ro
      - caddy_data:/data
      - caddy_config:/config
    networks:
      - edge

volumes:
  caddy_data:
  caddy_config:

networks:
  edge:
    external: true
EOF

    log "starting caddy..."
    (cd "$caddy_dir" && docker compose up -d)
}

# ── 9. Health checks ───────────────────────────────────────────────────────────
health_check() {
    local name="$1" url="$2"
    if curl -fsS -o /dev/null -m 10 "$url"; then
        log "$name OK — $url"
    else
        warn "$name did not respond at $url (may still be starting; retry in ~30s)"
    fi
}

# ── Main ───────────────────────────────────────────────────────────────────────
main() {
    install_docker
    install_bun
    ensure_edge_network

    sync_repo "$PRICEWATCH_REPO" "$APPS_DIR/pricewatch"
    sync_repo "$PRICEDROP_REPO" "$APPS_DIR/pricedrop"

    local envs_ready=0
    ensure_env_file "$APPS_DIR/pricewatch" "docs/env.example.txt" || envs_ready=1
    ensure_env_file "$APPS_DIR/pricedrop" "docs/env.example.txt" || envs_ready=1
    if [ "$envs_ready" -ne 0 ]; then
        die "fill in real secrets in the .env file(s) above, then re-run this script."
    fi

    build_frontend "$APPS_DIR/pricewatch/frontend" ""
    build_frontend "$APPS_DIR/pricedrop/frontend" ""

    compose_up "$APPS_DIR/pricewatch"
    compose_up "$APPS_DIR/pricedrop"

    setup_caddy

    log "waiting 10s for containers to settle..."
    sleep 10

    health_check "pricewatch (direct)" "http://localhost:8000/health"
    health_check "pricedrop (direct)" "http://localhost:8001/health"
    health_check "pricewatch (via Caddy/HTTPS)" "https://$PRICEWATCH_DOMAIN/health"
    health_check "pricedrop (via Caddy/HTTPS)" "https://$PRICEDROP_DOMAIN/health"

    log "done. See DEPLOY-RUNBOOK.md for the DNS + GitHub secrets checklist."
}

main "$@"
