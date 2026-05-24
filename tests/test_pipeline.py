from pathlib import Path

from app.pipeline import IngestionPipeline, load_result
from app.schemas.document import DocumentType


class NoopGenerator:
    async def enrich(self, document):
        document.key_takeaways = []
        document.glossary = []
        document.narration_script = []
        return document


async def test_pipeline_persists_final_document(temp_env: Path, sample_pdf: Path) -> None:
    from app.core.config import get_settings

    settings = get_settings()
    pipeline = IngestionPipeline(settings, generator=NoopGenerator())

    result = await pipeline.run("doc1", "sample.pdf", DocumentType.PDF, sample_pdf)
    document = load_result(result.result_path)

    assert document.document_metadata.document_id == "doc1"
    assert document.sections
    assert result.metrics["total_seconds"] >= 0
