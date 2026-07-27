# Builds the PriceWatch React SPA and serves the static output only (no
# source, no node_modules, no dev server) via nginx on a high port.
#
# Build context is the `frontend/` directory itself. This Dockerfile and its
# sibling nginx.conf (checked in here under deploy/frontend-static/ for
# version control) get copied alongside the frontend source at deploy time
# so the server-side `~/docker/PriceWatch/frontend/` directory is a
# self-contained build context — same convention as the backend's `app/`
# (docker-compose.yml: `build: ./frontend`).
#
# Build-time ARG VITE_API_BASE_URL bakes the backend's public origin into
# the bundle (Vite env vars are compile-time, not runtime).

# ── Stage 1: build ────────────────────────────────────────────────────────────
FROM oven/bun:1 AS builder

WORKDIR /build

COPY package.json bun.lock ./
RUN bun install --frozen-lockfile

COPY . .

ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN bun run build

# ── Stage 2: serve ─────────────────────────────────────────────────────────────
FROM nginx:1.27-alpine AS runtime

RUN rm -rf /usr/share/nginx/html/* /etc/nginx/conf.d/default.conf
COPY --from=builder /build/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/app.conf

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1:8080/ || exit 1
