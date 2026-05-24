# Intelligent Document Ingestion System

Production-shaped FastAPI service for ingesting PDF and PPTX documents, extracting structured JSON, and generating local-LLM outputs with Ollama.

This implementation follows a vertical-slice architecture: durable upload/status/result APIs, native PDF/PPTX parsing, PPTX speaker notes extraction, bounded local Ollama generation, Docker deployment, tests, and benchmarks.

## What It Supports

- PDF ingestion with PyMuPDF native text extraction
- PPTX ingestion with `python-pptx`
- PPTX speaker notes extraction through package XML
- Embedded image metadata extraction
- Local LLM generation through Ollama only
- Key takeaways
- Glossary
- Narration script
- Durable SQLite job state
- `POST /upload`
- `GET /status/{document_id}`
- `GET /result/{document_id}`

## First-Slice Limits

These are intentional scope decisions, not hidden behavior:

- OCR is deferred. Image-only pages are reported through `ocr_skipped` diagnostics.
- Legacy `.ppt` files are rejected with `415 Unsupported Media Type`.
- The queue is single-node SQLite. It is durable across API restarts, but not a distributed worker queue.
- The `fast` mode targets 50-page native-text documents in 30 seconds on suitable local hardware, but local Ollama latency depends on CPU/GPU, model, quantization, context size, and `OLLAMA_NUM_PARALLEL`.

Deferred items are tracked in [TODOS.md](TODOS.md).

## JSON Output Contract

Every completed result uses the required top-level shape:

```json
{
  "document_metadata": {},
  "sections": [],
  "slides": [],
  "images": [],
  "key_takeaways": [],
  "glossary": [],
  "narration_script": []
}
```

Nested objects include provenance and diagnostics so generated output can be traced back to pages or slides.

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
   |
   +--> PPTXParser -> slides + images + notes + diagnostics
   |
   v
Extractive evidence prefilter
   |
   v
LocalLLMOrchestrator -> Ollama /api/generate
   |
   v
FinalDocument JSON
   |
   v
GET /result/{document_id}
```

## Local Setup

Requirements:

- Python 3.11+
- Ollama running locally
- A local model such as `llama3` or `mistral`

Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Pull a local model:

```bash
ollama pull llama3
```

Run the API:

```bash
uvicorn app.main:app --reload
```

Open API docs:

```text
http://localhost:8000/docs
```

## Docker Setup

Create `.env`:

```bash
cp .env.example .env
```

Start services:

```bash
docker compose up --build
```

Pull the model into the Ollama container:

```bash
docker compose exec ollama ollama pull llama3
```

The API is available at:

```text
http://localhost:8000
```

## User Guide

Upload a document:

```bash
curl -F "file=@example.pdf" http://localhost:8000/upload
```

Response:

```json
{
  "document_id": "abc123",
  "status": "queued"
}
```

Check status:

```bash
curl http://localhost:8000/status/abc123
```

Fetch result after completion:

```bash
curl http://localhost:8000/result/abc123
```

Unsupported legacy PowerPoint:

```bash
curl -F "file=@deck.ppt" http://localhost:8000/upload
```

Returns `415` with:

```json
{
  "detail": {
    "code": "unsupported_file_type",
    "message": "Legacy .ppt files are not supported in this release. Upload .pptx instead.",
    "retryable": false
  }
}
```

## Developer Guide

Run tests:

```bash
pytest
```

Run lint:

```bash
ruff check .
```

Run benchmark:

```bash
python scripts/benchmark.py path/to/document.pdf
```

Benchmark records are appended to:

```text
storage/benchmarks.jsonl
```

## Configuration

Key environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `STORAGE_DIR` | `storage` | Uploads, results, SQLite DB |
| `DATABASE_URL` | `sqlite:///storage/app.db` | SQLite job database |
| `MAX_UPLOAD_MB` | `100` | Upload size limit |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API URL |
| `OLLAMA_MODEL` | `llama3` | Local model name |
| `OLLAMA_TIMEOUT_SECONDS` | `45` | Per-request LLM timeout |
| `PIPELINE_MODE` | `fast` | `fast` or `quality` |
| `FAST_MODE_MAX_CHARS` | `18000` | Evidence budget for fast mode |
| `QUALITY_MODE_MAX_CHARS` | `60000` | Evidence budget for quality mode |

## Module Map

```text
app/api/          FastAPI routes
app/core/         settings, logging, typed errors
app/storage/      file uploads and SQLite job store
app/parsers/      PDF and PPTX parsers
app/generation/   chunking, prompts, Ollama client, orchestration
app/pipeline.py   parse -> generate -> persist pipeline
app/worker.py     durable worker loop
tests/            unit, API, parser, and LLM contract tests
scripts/          benchmark tooling
```

## Error Handling

Expected failures use typed error codes persisted into job state:

- `unsupported_file_type`
- `file_too_large`
- `empty_file`
- `encrypted_pdf`
- `corrupt_document`
- `ollama_unavailable`
- `ollama_timeout`
- `llm_json_invalid`
- `result_not_ready`

Clients should use `/status/{document_id}` to inspect failed jobs.

## Performance Notes

Fast mode is designed to reduce local LLM latency:

1. Parse native text first.
2. Build a bounded extractive evidence set.
3. Run three JSON-generation prompts: takeaways, glossary, narration.
4. Persist timings in job metrics and result diagnostics.

Ollama concurrency is memory-sensitive. Increasing `OLLAMA_NUM_PARALLEL` can improve throughput but also increases memory use because parallel requests multiply context allocation.
