import os
import csv
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select, and_, func, true
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.db.session import async_session
from app.models.job import Job, JobStatus, JobType
from app.models.transaction import Transaction, TxType


def _ensure_dir() -> str:
    jobs_dir = os.path.abspath(settings.JOBS_DIR)
    os.makedirs(jobs_dir, exist_ok=True)
    return jobs_dir


def _parse_dt(v: Any) -> Optional[datetime]:
    """Accept datetime or ISO string; return tz-aware datetime (UTC) or None."""
    if v is None or v == "":
        return None
    if isinstance(v, datetime):
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
    if isinstance(v, str):
        s = v.strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    return None


def _parse_txtype(v: Any) -> Optional[TxType]:
    if v is None or v == "":
        return None
    if isinstance(v, TxType):
        return v
    try:
        return TxType(str(v))
    except Exception:
        return None


async def run_job(job_id: str) -> None:
    jobs_dir = _ensure_dir()

    async with async_session() as session:
        job = (await session.execute(select(Job).where(Job.id == job_id))).scalar_one_or_none()
        if not job:
            return

        job.status = JobStatus.running
        job.progress = 1
        job.started_at = datetime.now(timezone.utc)
        await session.commit()

        try:
            if job.type == JobType.export_transactions:
                await _export_transactions_csv(session, job, jobs_dir)
            else:
                raise RuntimeError(f"Unsupported job type: {job.type.value}")

            job.status = JobStatus.done
            job.progress = 100
            job.finished_at = datetime.now(timezone.utc)
            await session.commit()

        except Exception as e:
            # ВАЖНО: если до этого был SQL-эррор, транзакция "aborted"
            # Без rollback апдейт статуса не сохранится и job останется running.
            try:
                await session.rollback()
            except Exception:
                pass

            job.status = JobStatus.failed
            job.error = f"{type(e).__name__}: {e}"
            job.finished_at = datetime.now(timezone.utc)
            await session.commit()


async def _export_transactions_csv(session, job: Job, jobs_dir: str) -> None:
    p = job.params or {}
    conditions = []

    date_from = _parse_dt(p.get("date_from"))
    date_to = _parse_dt(p.get("date_to"))

    if date_from:
        conditions.append(Transaction.timestamp >= date_from)
    if date_to:
        conditions.append(Transaction.timestamp <= date_to)

    currency = p.get("currency")
    if currency and currency != "string":  # чтобы swagger-default не ломал смысл
        conditions.append(Transaction.currency == str(currency))

    client_id = p.get("client_id")
    try:
        if client_id is not None and int(client_id) > 0:
            conditions.append(Transaction.client_id == int(client_id))
    except (TypeError, ValueError):
        pass

    tx_type = _parse_txtype(p.get("type"))
    if tx_type:
        conditions.append(Transaction.type == tx_type)

    where_clause = and_(*conditions) if conditions else true()

    # count(*) теперь будет сравнивать timestamp с datetime, а не со строкой
    total = await session.scalar(select(func.count()).select_from(Transaction).where(where_clause))
    total = int(total or 0)

    filename = f"transactions_{job.id}.csv"
    path = os.path.join(jobs_dir, filename)

    chunk_size = 2000
    written = 0
    offset = 0

    with open(path, "w", newline="", encoding="utf-8") as f:
        f.write("\ufeff")  # BOM для Excel
        writer = csv.writer(f)

        while True:
            q = (
                select(Transaction)
                .where(where_clause)
                .order_by(Transaction.id.asc())
                .offset(offset)
                .limit(chunk_size)
            )
            rows = (await session.execute(q)).scalars().all()
            if not rows:
                break

            for tx in rows:
                writer.writerow([
                    tx.id,
                    tx.timestamp.isoformat() if tx.timestamp else "",
                    tx.type.value if hasattr(tx.type, "value") else str(tx.type),
                    tx.currency,
                    str(tx.amount),
                    str(tx.rate) if tx.rate is not None else "",
                    tx.client_id or "",
                    tx.comment or "",
                    tx.created_by,
                ])

            offset += len(rows)
            written += len(rows)

            if total > 0:
                job.progress = min(99, int(written * 99 / total))
            else:
                job.progress = 99

            await session.commit()

    stat = os.stat(path)
    job.result = {
        "path": path,
        "filename": "transactions.csv",
        "mime": "text/csv; charset=utf-8",
        "size": int(stat.st_size),
    }
    await session.commit()
