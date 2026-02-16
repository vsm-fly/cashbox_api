# =========================
# Base image
# =========================
FROM python:3.11-slim

# =========================
# Environment settings
# =========================
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# =========================
# Workdir
# =========================
WORKDIR /app

# =========================
# System dependencies
# =========================
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# =========================
# Install Python deps first (better cache)
# =========================
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# =========================
# Copy project code
# =========================
COPY . .

# =========================
# Expose port
# =========================
EXPOSE 8000

# =========================
# Start FastAPI with Uvicorn
# =========================
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
