# =========================
# Builder stage (deps build)
# =========================
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Ставим зависимости в отдельную директорию, чтобы потом скопировать в runtime
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# =========================
# Runtime stage (small image)
# =========================
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Копируем установленные зависимости из builder
COPY --from=builder /install /usr/local

# Копируем только код приложения
COPY app ./app
COPY alembic.ini .
COPY test_db.py .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
