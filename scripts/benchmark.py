import argparse
import asyncio
import json
import platform
import time
from pathlib import Path

from app.core.config import get_settings
from app.pipeline import IngestionPipeline
from app.storage.files import FileUploadManager


async def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark local document ingestion latency.")
    parser.add_argument("file", type=Path, help="PDF or PPTX file to ingest")
    parser.add_argument("--output", type=Path, default=Path("storage/benchmarks.jsonl"))
    args = parser.parse_args()

    settings = get_settings()
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    manager = FileUploadManager(settings)
    upload = manager.copy_fixture(args.file)

    started = time.perf_counter()
    result = await IngestionPipeline(settings).run(
        upload.document_id,
        upload.filename,
        upload.document_type,
        upload.path,
    )
    total = time.perf_counter() - started

    record = {
        "document_id": upload.document_id,
        "filename": upload.filename,
        "mode": settings.pipeline_mode,
        "model": settings.ollama_model,
        "ollama_base_url": settings.ollama_base_url,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "metrics": result.metrics,
        "wall_seconds": round(total, 3),
        "result_path": str(result.result_path),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("a", encoding="utf-8") as out:
        out.write(json.dumps(record, sort_keys=True) + "\n")
    print(json.dumps(record, indent=2, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())
