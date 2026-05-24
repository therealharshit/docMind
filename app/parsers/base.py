from pathlib import Path

from app.schemas.document import FinalDocument, ProcessingMode


class DocumentParser:
    """Parser interface for a stored document."""

    def parse(
        self,
        document_id: str,
        filename: str,
        path: Path,
        processing_mode: ProcessingMode,
    ) -> FinalDocument:
        raise NotImplementedError
