from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select

from app.core.deps import get_current_user
from app.db.session import async_session
from app.models.job import Job, JobType, JobStatus
from app.models.user import User
from app.schemas.jobs import ExportTransactionsParams, JobCreated, JobOut
from app.services.job_runner import run_job

# Вариант A: защита на уровне роутера
router = APIRouter(dependencies=[Depends(get_current_user)])


def _is_admin(user: User) -> bool:
    # user.role может быть Enum или строка — приводим к строке
    return str(getattr(user.role, "value", user.role)) == "admin"


async def _get_job_or_404(session, job_id: str, user: User) -> Job:
    job = (await session.execute(select(Job).where(Job.id == job_id))).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.created_by != user.id and not _is_admin(user):
        # чтобы не раскрывать, что job существует
        raise HTTPException(status_code=404, detail="Job not found")

    return job


@router.post("/exports/transactions", response_model=JobCreated)
async def create_export_transactions_job(
    payload: ExportTransactionsParams,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
):
    async with async_session() as session:
        job = Job(
            type=JobType.export_transactions,
            status=JobStatus.queued,
            progress=0,
            created_by=user.id,
            params=payload.model_dump(mode="json"),
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)

    background_tasks.add_task(run_job, str(job.id))
    return JobCreated(job_id=job.id, status=job.status.value)


@router.get("/{job_id}", response_model=JobOut)
async def get_job(job_id: str, user: User = Depends(get_current_user)):
    async with async_session() as session:
        job = await _get_job_or_404(session, job_id, user)

        return JobOut(
            job_id=job.id,
            type=job.type.value,
            status=job.status.value,
            progress=job.progress,
            created_at=job.created_at,
            started_at=job.started_at,
            finished_at=job.finished_at,
            error=job.error,
            result=job.result,
        )


@router.get("/{job_id}/download")
async def download_job_result(job_id: str, user: User = Depends(get_current_user)):
    async with async_session() as session:
        job = await _get_job_or_404(session, job_id, user)

        if job.status != JobStatus.done:
            raise HTTPException(status_code=409, detail=f"Job not done (status={job.status.value})")
        if not job.result or "path" not in job.result:
            raise HTTPException(status_code=404, detail="No result file")

        return FileResponse(
            path=job.result["path"],
            media_type=job.result.get("mime", "text/csv"),
            filename=job.result.get("filename", "transactions.csv"),
        )
