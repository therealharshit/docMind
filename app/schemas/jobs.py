from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class JobStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class UploadResponse(BaseModel):
    document_id: str
    status: JobStatus


class ErrorPayload(BaseModel):
    code: str
    message: str
    retryable: bool = False


class StatusResponse(BaseModel):
    document_id: str
    status: JobStatus
    filename: str
    created_at: str
    updated_at: str
    error: ErrorPayload | None = None
    metrics: dict[str, Any] = {}
