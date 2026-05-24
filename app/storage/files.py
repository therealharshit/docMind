import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import Settings
from app.core.errors import ErrorCode, UnsupportedFileTypeError, AppError
from app.schemas.document import DocumentType


ALLOWED_EXTENSIONS = {".pdf": DocumentType.PDF, ".pptx": DocumentType.PPTX}
REJECTED_EXTENSIONS = {".ppt"}


class StoredUpload:
    def __init__(self, document_id: str, filename: str, document_type: DocumentType, path: Path) -> None:
        self.document_id = document_id
        self.filename = filename
        self.document_type = document_type
        self.path = path


class FileUploadManager:
    """Validates and stores uploads using a generated document id."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.settings.upload_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, upload: UploadFile) -> StoredUpload:
        filename = Path(upload.filename or "").name
        suffix = Path(filename).suffix.lower()
        if suffix in REJECTED_EXTENSIONS:
            raise UnsupportedFileTypeError(
                "Legacy .ppt files are not supported in this release. Upload .pptx instead."
            )
        if suffix not in ALLOWED_EXTENSIONS:
            raise UnsupportedFileTypeError("Only PDF and PPTX files are supported.")

        document_id = uuid4().hex
        target_dir = self.settings.upload_dir / document_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / filename

        size = 0
        max_bytes = self.settings.max_upload_mb * 1024 * 1024
        with target.open("wb") as out:
            while chunk := await upload.read(1024 * 1024):
                size += len(chunk)
                if size > max_bytes:
                    target.unlink(missing_ok=True)
                    raise AppError(
                        ErrorCode.FILE_TOO_LARGE,
                        f"Upload exceeds {self.settings.max_upload_mb} MB limit.",
                        retryable=False,
                    )
                out.write(chunk)

        if size == 0:
            target.unlink(missing_ok=True)
            raise AppError(ErrorCode.EMPTY_FILE, "Uploaded file is empty.", retryable=False)

        return StoredUpload(document_id, filename, ALLOWED_EXTENSIONS[suffix], target)

    def copy_fixture(self, source: Path, filename: str | None = None) -> StoredUpload:
        """Store a local fixture. Used by tests and benchmarks."""

        suffix = source.suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise UnsupportedFileTypeError("Only PDF and PPTX files are supported.")
        document_id = uuid4().hex
        target_dir = self.settings.upload_dir / document_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / (filename or source.name)
        shutil.copyfile(source, target)
        return StoredUpload(document_id, target.name, ALLOWED_EXTENSIONS[suffix], target)
