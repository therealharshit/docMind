# Developer Guide

This guide covers repository layout, development commands, testing, and implementation notes.

## Module Map

```text
app/api/          FastAPI routes
app/core/         settings, logging, typed errors
app/storage/      file uploads and SQLite job store
app/parsers/      PDF and PPTX parsers
app/generation/   chunking, prompts, LLM clients (Ollama + Google), factory, orchestration
app/pipeline.py   parse -> generate -> persist pipeline
app/worker.py     durable worker loop
tests/            unit, API, parser, and LLM contract tests
scripts/          benchmark tooling
```

## Development Commands

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the API:

```bash
uvicorn app.main:app --reload
```

Run tests and lint:

```bash
pytest
ruff check .
```

Run a benchmark:

```bash
python scripts/benchmark.py path/to/document.pdf
```

Benchmark records are appended to `storage/benchmarks.jsonl`.

## Architecture

```text
POST /upload
   |
   v
FileUploadManager
   |
   v
SQLite JobStore  ----->  GET /status/{document_id}
   |
   v
Worker loop
   |
   +--> PDFParser  -> sections + images + diagnostics
   +--> PPTXParser -> slides + images + notes + diagnostics
   |
   v
Extractive evidence prefilter
   |
   v
LocalLLMOrchestrator -> LLM client (Ollama or Google GenAI via factory)
   |
   v
FinalDocument JSON -> GET /result/{document_id}
```

## Error Handling

Expected failures use typed errors from `app/core/errors.py` and are persisted into job state:

- `unsupported_file_type`
- `file_too_large`
- `empty_file`
- `encrypted_pdf`
- `corrupt_document`
- `ollama_unavailable`
- `ollama_timeout`
- `google_api_error`
- `google_timeout`
- `llm_provider_invalid`
- `llm_json_invalid`
- `result_not_ready`

Clients inspect failures through `/status/{document_id}`.

## Testing Notes

Tests use `pytest`, `pytest-asyncio`, and `pytest-cov`. LLM behavior is tested with fake clients (both Ollama and Google) so CI stays deterministic. The shared response normalization in `_response.py` has dedicated tests covering JSON parsing, markdown stripping, and schema coercion. Live model behavior belongs in benchmark runs.

## Performance Notes

Fast mode reduces LLM latency by parsing native text first, building a bounded extractive evidence set, and running three JSON prompts in parallel.

- **Ollama:** Concurrency is memory-sensitive; increasing `OLLAMA_NUM_PARALLEL` can improve throughput but also multiplies context memory use.
- **Google GenAI:** Latency depends on network and API quotas. The `gemini-2.0-flash` model is recommended for speed and cost-effectiveness.
