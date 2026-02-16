# =========================
# Builder
# =========================
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# deps for building wheels (kept only in builder)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# pip cache for faster rebuilds (BuildKit)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --prefix=/install -r requirements.txt


# =========================
# Runtime
# =========================
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# create non-root user
RUN addgroup --system app && adduser --system --ingroup app app

# install runtime deps (curl for healthcheck; optional but useful)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# copy installed python packages from builder
COPY --from=builder /install /usr/local

# copy app code (copy only what you need)
COPY app ./app
COPY alembic.ini .
COPY test_db.py .

# permissions
RUN chown -R app:app /app
USER app

EXPOSE 8000

# healthcheck (expects /docs to be available; you can change to /api/v1/health if you add it)
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://localhost:8000/docs >/dev/null || exit 1

# production command
CMD ["gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "--workers", "2"]
