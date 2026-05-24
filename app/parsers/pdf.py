from pathlib import Path

import fitz

from app.core.errors import ErrorCode, ParserError
from app.parsers.base import DocumentParser
from app.schemas.document import (
    DocumentMetadata,
    DocumentType,
    ExtractedImage,
    FinalDocument,
    ProcessingMode,
    Provenance,
    Section,
)


class PDFParser(DocumentParser):
    """Extract native PDF text and embedded image metadata with PyMuPDF."""

    def parse(
        self,
        document_id: str,
        filename: str,
        path: Path,
        processing_mode: ProcessingMode,
    ) -> FinalDocument:
        try:
            doc = fitz.open(path)
        except Exception as exc:
            raise ParserError(ErrorCode.CORRUPT_DOCUMENT, "PDF could not be opened.") from exc

        try:
            if doc.is_encrypted:
                raise ParserError(ErrorCode.ENCRYPTED_PDF, "Encrypted PDFs are not supported.")

            metadata = doc.metadata or {}
            sections: list[Section] = []
            images: list[ExtractedImage] = []
            low_text_pages: list[int] = []

            for page_index, page in enumerate(doc, start=1):
                text = page.get_text("text", sort=True).strip()
                if len(text) < 40:
                    low_text_pages.append(page_index)
                header, body = self._split_header_body(text)
                if body:
                    sections.append(
                        Section(
                            index=len(sections) + 1,
                            header=header,
                            body_text=body,
                            provenance=[
                                Provenance(
                                    source_type="pdf_page",
                                    page_number=page_index,
                                    confidence=1.0,
                                )
                            ],
                        )
                    )

                for image_index, image_info in enumerate(page.get_images(full=True), start=1):
                    xref = image_info[0]
                    width = image_info[2]
                    height = image_info[3]
                    ext = image_info[7] if len(image_info) > 7 else None
                    images.append(
                        ExtractedImage(
                            image_id=f"{document_id}-p{page_index}-i{image_index}-{xref}",
                            source_type="pdf",
                            page_number=page_index,
                            extension=ext,
                            width=width,
                            height=height,
                            metadata={"xref": xref},
                        )
                    )

            return FinalDocument(
                document_metadata=DocumentMetadata(
                    document_id=document_id,
                    filename=filename,
                    document_type=DocumentType.PDF,
                    page_count=doc.page_count,
                    author=metadata.get("author") or None,
                    title=metadata.get("title") or None,
                    subject=metadata.get("subject") or None,
                    created_at=metadata.get("creationDate") or None,
                    parser="pymupdf",
                    processing_mode=processing_mode,
                    diagnostics={
                        "ocr_skipped": True,
                        "ocr_status": "deferred_in_first_slice",
                        "low_text_pages": low_text_pages,
                    },
                ),
                sections=sections,
                images=images,
            )
        finally:
            doc.close()

    def _split_header_body(self, text: str) -> tuple[str | None, str]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return None, ""
        if len(lines) == 1:
            return None, lines[0]
        first = lines[0]
        if len(first) <= 120:
            return first, "\n".join(lines[1:])
        return None, "\n".join(lines)
