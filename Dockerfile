# ── Stage 1: build dependencies ───────────────────────────────────────────────
FROM python:3.10-slim AS builder

WORKDIR /build

# Install build tools needed by some packages (psycopg binary, argon2-cffi)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
# Install project deps into an isolated prefix so we can copy only that layer
RUN pip install --no-cache-dir --prefix=/install ".[dev]" 2>/dev/null || \
    pip install --no-cache-dir --prefix=/install .


# ── Stage 2: runtime image ────────────────────────────────────────────────────
FROM python:3.10-slim AS runtime

# Security: run as non-root
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

# Runtime system lib for psycopg (libpq)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY app/ ./app/

# Non-root ownership
RUN chown -R appuser:appgroup /app
USER appuser

EXPOSE 8000

# Healthcheck — pings /health every 30s, fails after 3 misses
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Single worker to avoid duplicate APScheduler instances.
# See README "Multi-worker caveat" if you need to scale.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
