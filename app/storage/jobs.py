import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.schemas.document import DocumentType
from app.schemas.jobs import ErrorPayload, JobStatus, StatusResponse


def utcnow() -> str:
    return datetime.now(UTC).isoformat()


class JobRecord:
    def __init__(
        self,
        document_id: str,
        filename: str,
        document_type: DocumentType,
        file_path: Path,
        status: JobStatus,
    ) -> None:
        self.document_id = document_id
        self.filename = filename
        self.document_type = document_type
        self.file_path = file_path
        self.status = status


class JobStore:
    """SQLite-backed durable job state.

    Request flow:
      /upload -> create_job(queued)
              -> worker claim_next_job()
              -> mark_completed(result_path) OR mark_failed(error)
              -> /status and /result read persisted state
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path, timeout=30, isolation_level=None)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            yield conn
        finally:
            conn.close()

    def initialize(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    document_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    document_type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    status TEXT NOT NULL,
                    result_path TEXT,
                    error_json TEXT,
                    metrics_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status, created_at)")

    def create_job(
        self, document_id: str, filename: str, document_type: DocumentType, file_path: Path
    ) -> None:
        now = utcnow()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO jobs (
                    document_id, filename, document_type, file_path, status,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (document_id, filename, document_type.value, str(file_path), JobStatus.QUEUED, now, now),
            )

    def claim_next_job(self) -> JobRecord | None:
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                """
                SELECT * FROM jobs
                WHERE status = ?
                ORDER BY created_at ASC
                LIMIT 1
                """,
                (JobStatus.QUEUED,),
            ).fetchone()
            if row is None:
                conn.execute("COMMIT")
                return None
            conn.execute(
                "UPDATE jobs SET status = ?, updated_at = ? WHERE document_id = ?",
                (JobStatus.PROCESSING, utcnow(), row["document_id"]),
            )
            conn.execute("COMMIT")
            return self._record_from_row(row, JobStatus.PROCESSING)

    def mark_completed(self, document_id: str, result_path: Path, metrics: dict[str, Any]) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE jobs
                SET status = ?, result_path = ?, metrics_json = ?, error_json = NULL, updated_at = ?
                WHERE document_id = ?
                """,
                (
                    JobStatus.COMPLETED,
                    str(result_path),
                    json.dumps(metrics, sort_keys=True),
                    utcnow(),
                    document_id,
                ),
            )

    def mark_failed(
        self, document_id: str, code: str, message: str, retryable: bool, metrics: dict[str, Any] | None = None
    ) -> None:
        error_json = json.dumps({"code": code, "message": message, "retryable": retryable})
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE jobs
                SET status = ?, error_json = ?, metrics_json = ?, updated_at = ?
                WHERE document_id = ?
                """,
                (
                    JobStatus.FAILED,
                    error_json,
                    json.dumps(metrics or {}, sort_keys=True),
                    utcnow(),
                    document_id,
                ),
            )

    def get_status(self, document_id: str) -> StatusResponse | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE document_id = ?", (document_id,)).fetchone()
        if row is None:
            return None
        error = ErrorPayload(**json.loads(row["error_json"])) if row["error_json"] else None
        return StatusResponse(
            document_id=row["document_id"],
            status=JobStatus(row["status"]),
            filename=row["filename"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            error=error,
            metrics=json.loads(row["metrics_json"] or "{}"),
        )

    def get_result_path(self, document_id: str) -> Path | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT result_path FROM jobs WHERE document_id = ? AND status = ?",
                (document_id, JobStatus.COMPLETED),
            ).fetchone()
        if row is None or row["result_path"] is None:
            return None
        return Path(row["result_path"])

    def _record_from_row(self, row: sqlite3.Row, status: JobStatus | None = None) -> JobRecord:
        return JobRecord(
            document_id=row["document_id"],
            filename=row["filename"],
            document_type=DocumentType(row["document_type"]),
            file_path=Path(row["file_path"]),
            status=status or JobStatus(row["status"]),
        )
