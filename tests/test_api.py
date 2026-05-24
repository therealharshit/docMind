from pathlib import Path

from fastapi.testclient import TestClient


def test_upload_rejects_legacy_ppt(temp_env: Path, tmp_path: Path) -> None:
    from app.core.config import get_settings
    from app.main import create_app

    get_settings.cache_clear()
    app = create_app()
    client = TestClient(app)
    path = tmp_path / "legacy.ppt"
    path.write_bytes(b"legacy")

    with path.open("rb") as upload:
        response = client.post("/upload", files={"file": ("legacy.ppt", upload, "application/vnd.ms-powerpoint")})

    assert response.status_code == 415
    assert response.json()["detail"]["code"] == "unsupported_file_type"


def test_status_missing_returns_404(temp_env: Path) -> None:
    from app.core.config import get_settings
    from app.main import create_app

    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.get("/status/missing")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "job_not_found"
