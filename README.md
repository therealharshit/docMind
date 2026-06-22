# Intelligent Document Ingestion System

Production-shaped FastAPI service for ingesting PDF and PPTX documents, extracting structured JSON, and generating LLM-powered outputs with Ollama (local) or Google Generative AI (cloud).

This implementation follows a vertical-slice architecture: durable upload/status/result APIs, native PDF/PPTX parsing, PPTX speaker notes extraction, configurable LLM generation, Docker deployment, tests, and benchmarks.

## Documentation

- [User Guide](docs/user-guide.md) — setup, Docker, API usage, supported files, and output format.
- [Developer Guide](docs/developer-guide.md) — module map, commands, architecture, testing, and performance notes.

## What It Supports

- PDF ingestion with PyMuPDF native text extraction
- PPTX ingestion with `python-pptx`
- PPTX speaker notes extraction through package XML
- Embedded image metadata extraction
- LLM generation through Ollama (local) or Google Generative AI (cloud)
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

## Quick Start

Requirements:

- Python 3.11+
- **Option A (local):** Ollama running locally with a model such as `llama3` or `mistral`
- **Option B (cloud):** A Google Generative AI API key

Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Pull a local model (if using Ollama):

```bash
ollama pull llama3
```

Or configure Google Generative AI instead:

```bash
# In your .env file:
LLM_PROVIDER=google
GOOGLE_API_KEY=your-api-key-here
GOOGLE_MODEL=gemini-2.0-flash
```

Run the API:

```bash
uvicorn app.main:app --reload
```

Open API docs:

```text
http://localhost:8000/docs
```

## Docker

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

## API Example

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

## Development

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

See the [Developer Guide](docs/developer-guide.md) for the architecture, module map, testing notes, and benchmark details.

## Configuration

Key environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `STORAGE_DIR` | `storage` | Uploads, results, SQLite DB |
| `DATABASE_URL` | `sqlite:///storage/app.db` | SQLite job database |
| `MAX_UPLOAD_MB` | `100` | Upload size limit |
| `LLM_PROVIDER` | `ollama` | LLM backend: `ollama` or `google` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API URL |
| `OLLAMA_MODEL` | `llama3` | Local model name |
| `OLLAMA_TIMEOUT_SECONDS` | `45` | Per-request LLM timeout |
| `GOOGLE_API_KEY` | _(empty)_ | Google Generative AI API key (required when provider is `google`) |
| `GOOGLE_MODEL` | `gemini-2.0-flash` | Google model name |
| `PIPELINE_MODE` | `fast` | `fast` or `quality` |
| `FAST_MODE_MAX_CHARS` | `18000` | Evidence budget for fast mode |
| `QUALITY_MODE_MAX_CHARS` | `60000` | Evidence budget for quality mode |

## License

MIT © 2026 Harshit Verma. See [LICENSE](LICENSE) for details.
