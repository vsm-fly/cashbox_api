# Cashbox API (FastAPI + PostgreSQL + Jobs)

## Quick start (dev)

1) Start Postgres:
```bash
docker compose up -d db
```

2) Create venv & install deps:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3) Run migrations:
```bash
alembic upgrade head
```

4) Create an admin user:
```bash
python -m app.scripts.create_admin --email admin@example.com --password admin
```

5) Run API:
```bash
uvicorn app.main:app --reload
```

Open docs: http://127.0.0.1:8000/docs

## Auth
- `POST /api/v1/auth/login` -> access token (JWT)
- Use `Authorization: Bearer <token>`

## Jobs
- `POST /api/v1/jobs/exports/transactions` -> returns `job_id`
- `GET /api/v1/jobs/{job_id}` -> status
- `GET /api/v1/jobs/{job_id}/download` -> CSV when done
