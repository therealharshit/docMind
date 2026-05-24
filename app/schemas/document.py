from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class DocumentType(StrEnum):
    PDF = "pdf"
    PPTX = "pptx"


class ProcessingMode(StrEnum):
    FAST = "fast"
    QUALITY = "quality"


class Provenance(BaseModel):
    source_type: str
    page_number: int | None = None
    slide_number: int | None = None
    confidence: float | None = None


class DocumentMetadata(BaseModel):
    document_id: str
    filename: str
    document_type: DocumentType
    page_count: int | None = None
    slide_count: int | None = None
    author: str | None = None
    title: str | None = None
    subject: str | None = None
    created_at: str | None = None
    parser: str
    processing_mode: ProcessingMode
    diagnostics: dict[str, Any] = Field(default_factory=dict)


class Section(BaseModel):
    index: int
    header: str | None = None
    body_text: str
    provenance: list[Provenance] = Field(default_factory=list)


class Slide(BaseModel):
    slide_number: int
    title: str | None = None
    body_text: str
    notes: str | None = None
    provenance: list[Provenance] = Field(default_factory=list)
    diagnostics: dict[str, Any] = Field(default_factory=dict)


class ExtractedImage(BaseModel):
    image_id: str
    source_type: str
    page_number: int | None = None
    slide_number: int | None = None
    extension: str | None = None
    width: int | None = None
    height: int | None = None
    path: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class GeneratedItem(BaseModel):
    text: str
    provenance: list[Provenance] = Field(default_factory=list)


class GlossaryItem(BaseModel):
    term: str
    definition: str
    provenance: list[Provenance] = Field(default_factory=list)


class FinalDocument(BaseModel):
    document_metadata: DocumentMetadata
    sections: list[Section] = Field(default_factory=list)
    slides: list[Slide] = Field(default_factory=list)
    images: list[ExtractedImage] = Field(default_factory=list)
    key_takeaways: list[GeneratedItem] = Field(default_factory=list)
    glossary: list[GlossaryItem] = Field(default_factory=list)
    narration_script: list[GeneratedItem] = Field(default_factory=list)
