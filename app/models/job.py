import enum
import uuid
from datetime import datetime

from sqlalchemy import Enum, Integer, ForeignKey, DateTime, func, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class JobType(str, enum.Enum):
    export_transactions = "export_transactions"
    print_ko1 = "print_ko1"
    print_ko2 = "print_ko2"


class JobStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    done = "done"
    failed = "failed"
    canceled = "canceled"


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type: Mapped[JobType] = mapped_column(Enum(JobType, name="job_type"), index=True)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status"),
        index=True,
        default=JobStatus.queued,
    )
    progress: Mapped[int] = mapped_column(Integer, default=0)

    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    params: Mapped[dict] = mapped_column(JSONB, default=dict)
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_by: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
