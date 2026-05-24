from pathlib import Path

import pytest

from app.core.errors import UnsupportedFileTypeError
from app.storage.files import FileUploadManager


def test_copy_fixture_rejects_unsupported_type(temp_env: Path, tmp_path: Path) -> None:
    from app.core.config import get_settings

    path = tmp_path / "notes.txt"
    path.write_text("hello", encoding="utf-8")

    with pytest.raises(UnsupportedFileTypeError):
        FileUploadManager(get_settings()).copy_fixture(path)
