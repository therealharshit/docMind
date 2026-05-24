from pathlib import Path

import pytest

from app.core.errors import ParserError
from app.parsers.pdf import PDFParser
from app.parsers.pptx import PPTXParser
from app.schemas.document import ProcessingMode


def test_pdf_parser_extracts_text_and_ocr_diagnostic(sample_pdf: Path) -> None:
    document = PDFParser().parse("doc1", "sample.pdf", sample_pdf, ProcessingMode.FAST)

    assert document.document_metadata.page_count == 1
    assert document.sections
    assert document.sections[0].header == "Quarterly Plan"
    assert document.document_metadata.diagnostics["ocr_skipped"] is True


def test_pdf_parser_rejects_corrupt_pdf(tmp_path: Path) -> None:
    path = tmp_path / "bad.pdf"
    path.write_text("not a pdf", encoding="utf-8")

    with pytest.raises(ParserError):
        PDFParser().parse("doc1", "bad.pdf", path, ProcessingMode.FAST)


def test_pptx_parser_extracts_slide_notes(sample_pptx: Path) -> None:
    document = PPTXParser().parse("doc1", "sample.pptx", sample_pptx, ProcessingMode.FAST)

    assert document.document_metadata.slide_count == 1
    assert document.slides[0].title == "Roadmap"
    assert "benchmark target" in (document.slides[0].notes or "")
