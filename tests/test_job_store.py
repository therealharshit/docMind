from pathlib import Path

from app.schemas.document import DocumentType
from app.schemas.jobs import JobStatus
from app.storage.jobs import JobStore


def test_job_store_claims_and_persists_failure(tmp_path: Path) -> None:
    store = JobStore(tmp_path / "jobs.db")
    store.create_job("doc1", "a.pdf", DocumentType.PDF, tmp_path / "a.pdf")

    claimed = store.claim_next_job()

    assert claimed is not None
    assert claimed.document_id == "doc1"
    assert claimed.status == JobStatus.PROCESSING

    store.mark_failed("doc1", "parser_failed", "bad file", retryable=False)
    status = store.get_status("doc1")

    assert status is not None
    assert status.status == JobStatus.FAILED
    assert status.error is not None
    assert status.error.code == "parser_failed"
