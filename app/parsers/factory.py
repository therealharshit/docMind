from app.parsers.base import DocumentParser
from app.parsers.pdf import PDFParser
from app.parsers.pptx import PPTXParser
from app.schemas.document import DocumentType


def parser_for(document_type: DocumentType) -> DocumentParser:
    if document_type == DocumentType.PDF:
        return PDFParser()
    if document_type == DocumentType.PPTX:
        return PPTXParser()
    raise ValueError(f"Unsupported document type: {document_type}")
