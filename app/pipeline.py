import json
import time
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.generation.orchestrator import LocalLLMOrchestrator
from app.parsers.factory import parser_for
from app.schemas.document import DocumentType, FinalDocument, ProcessingMode


class PipelineResult:
    def __init__(self, result_path: Path, metrics: dict[str, Any]) -> None:
        self.result_path = result_path
        self.metrics = metrics


class IngestionPipeline:
    """Parse a stored document, enrich it with local LLM outputs, and persist JSON."""

    def __init__(
        self,
        settings: Settings,
        generator: LocalLLMOrchestrator | None = None,
    ) -> None:
        self.settings = settings
        self.generator = generator or LocalLLMOrchestrator(settings)
        self.settings.result_dir.mkdir(parents=True, exist_ok=True)

    async def run(
        self,
        document_id: str,
        filename: str,
        document_type: DocumentType,
        file_path: Path,
    ) -> PipelineResult:
        started = time.perf_counter()
        mode = ProcessingMode(self.settings.pipeline_mode)

        parse_started = time.perf_counter()
        parsed = parser_for(document_type).parse(document_id, filename, file_path, mode)
        parse_seconds = time.perf_counter() - parse_started

        generation_started = time.perf_counter()
        final_document = await self.generator.enrich(parsed)
        generation_seconds = time.perf_counter() - generation_started

        result_path = self.settings.result_dir / f"{document_id}.json"
        result_path.write_text(
            json.dumps(final_document.model_dump(mode="json"), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        total_seconds = time.perf_counter() - started
        final_document.document_metadata.diagnostics["timings"] = {
            "parse_seconds": round(parse_seconds, 3),
            "generation_seconds": round(generation_seconds, 3),
            "total_seconds": round(total_seconds, 3),
        }
        result_path.write_text(
            json.dumps(final_document.model_dump(mode="json"), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return PipelineResult(
            result_path=result_path,
            metrics={
                "parse_seconds": round(parse_seconds, 3),
                "generation_seconds": round(generation_seconds, 3),
                "total_seconds": round(total_seconds, 3),
            },
        )


def load_result(path: Path) -> FinalDocument:
    return FinalDocument.model_validate_json(path.read_text(encoding="utf-8"))
