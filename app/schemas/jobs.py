from datetime import datetime
from pydantic import BaseModel
from typing import Literal
import uuid


class ExportTransactionsParams(BaseModel):
    date_from: datetime | None = None
    date_to: datetime | None = None
    currency: str | None = None
    client_id: int | None = None
    type: Literal["income", "expense"] | None = None


class JobCreated(BaseModel):
    job_id: uuid.UUID
    status: str


class JobOut(BaseModel):
    job_id: uuid.UUID
    type: str
    status: str
    progress: int
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    error: str | None
    result: dict | None
