from pathlib import Path

from fastapi.testclient import TestClient

from app.schemas.document import DocumentType


def test_upload_rejects_legacy_ppt(temp_env: Path, tmp_path: Path) -> None:
    from app.core.config import get_settings
    from app.main import create_app

    get_settings.cache_clear()
    app = create_app()
    path = tmp_path / "legacy.ppt"
    path.write_bytes(b"legacy")

    with TestClient(app) as client, path.open("rb") as upload:
        response = client.post(
            "/upload",
            files={"file": ("legacy.ppt", upload, "application/vnd.ms-powerpoint")},
        )

    assert response.status_code == 415
    assert response.json()["detail"]["code"] == "unsupported_file_type"


def test_status_missing_returns_404(temp_env: Path) -> None:
    from app.core.config import get_settings
    from app.main import create_app

    get_settings.cache_clear()
    with TestClient(create_app()) as client:
        response = client.get("/status/missing")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "job_not_found"


def test_result_pending_returns_409(temp_env: Path, tmp_path: Path) -> None:
    from app.core.config import get_settings
    from app.main import create_app

    get_settings.cache_clear()
    file_path = tmp_path / "queued.pdf"
    file_path.write_bytes(b"%PDF")

    with TestClient(create_app()) as client:
        client.app.state.job_store.create_job("doc1", "queued.pdf", DocumentType.PDF, file_path)
        response = client.get("/result/doc1")

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "result_not_ready"


def test_result_completed_returns_json(temp_env: Path, tmp_path: Path) -> None:
    from app.core.config import get_settings
    from app.main import create_app

    get_settings.cache_clear()
    result_path = tmp_path / "doc1.json"
    result_path.write_text(
        """
        {
          "document_metadata": {
            "document_id": "doc1",
            "filename": "done.pdf",
            "document_type": "pdf",
            "page_count": 1,
            "parser": "test",
            "processing_mode": "fast",
            "diagnostics": {}
          },
          "sections": [],
          "slides": [],
          "images": [],
          "key_takeaways": [],
          "glossary": [],
          "narration_script": []
        }
        """,
        encoding="utf-8",
    )

    with TestClient(create_app()) as client:
        client.app.state.job_store.create_job(
            "doc1",
            "done.pdf",
            DocumentType.PDF,
            tmp_path / "done.pdf",
        )
        client.app.state.job_store.mark_completed("doc1", result_path, {"total_seconds": 1.0})
        response = client.get("/result/doc1")

    assert response.status_code == 200
    assert response.json()["document_metadata"]["document_id"] == "doc1"
