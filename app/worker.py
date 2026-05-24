import asyncio
import logging
from contextlib import suppress

from app.core.config import Settings
from app.core.errors import AppError, ErrorCode
from app.pipeline import IngestionPipeline
from app.storage.jobs import JobStore

logger = logging.getLogger(__name__)


class Worker:
    """Single-process worker loop that claims and processes queued jobs."""

    def __init__(
        self,
        settings: Settings,
        job_store: JobStore,
        pipeline: IngestionPipeline | None = None,
    ) -> None:
        self.settings = settings
        self.job_store = job_store
        self.pipeline = pipeline or IngestionPipeline(settings)
        self._stop_event = asyncio.Event()
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self.run_forever())

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task is not None:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task

    async def run_forever(self) -> None:
        while not self._stop_event.is_set():
            job = self.job_store.claim_next_job()
            if job is None:
                await asyncio.sleep(self.settings.worker_poll_seconds)
                continue
            logger.info("processing document_id=%s filename=%s", job.document_id, job.filename)
            try:
                result = await self.pipeline.run(
                    job.document_id,
                    job.filename,
                    job.document_type,
                    job.file_path,
                )
            except AppError as exc:
                logger.warning("job failed document_id=%s code=%s", job.document_id, exc.code)
                self.job_store.mark_failed(
                    job.document_id,
                    exc.code,
                    exc.message,
                    exc.retryable,
                )
            except Exception:
                logger.exception("unexpected job failure document_id=%s", job.document_id)
                self.job_store.mark_failed(
                    job.document_id,
                    ErrorCode.INTERNAL_ERROR,
                    "Unexpected ingestion failure.",
                    retryable=True,
                )
            else:
                self.job_store.mark_completed(job.document_id, result.result_path, result.metrics)
                logger.info("job completed document_id=%s", job.document_id)
