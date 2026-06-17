# User Guide

This guide covers running the Intelligent Document Ingestion System and using its API.

## Requirements

- Python 3.11+
- **Option A — Local (Ollama):** Ollama running locally with a model such as `llama3` or `mistral`
- **Option B — Cloud (Google):** A Google Generative AI API key (no local GPU needed)

## Local Setup (Ollama)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
ollama pull llama3
uvicorn app.main:app --reload
```

## Local Setup (Google Generative AI)

If you don't have a powerful machine for local models, use Google's cloud API instead:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set:

```env
LLM_PROVIDER=google
GOOGLE_API_KEY=your-api-key-here
GOOGLE_MODEL=gemini-2.0-flash
```

Then start the API:

```bash
uvicorn app.main:app --reload
```

API docs are available at:

```text
http://localhost:8000/docs
```

## Docker Setup

```bash
cp .env.example .env
docker compose up --build
docker compose exec ollama ollama pull llama3
```

The API runs at:

```text
http://localhost:8000
```

## Upload A Document

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

## Supported Files

- `.pdf`
- `.pptx`

Legacy `.ppt` files are rejected with `415 Unsupported Media Type`:

```json
{
  "detail": {
    "code": "unsupported_file_type",
    "message": "Legacy .ppt files are not supported in this release. Upload .pptx instead.",
    "retryable": false
  }
}
```

## Output Format

Completed jobs return:

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

Nested items include provenance and diagnostics for tracing content back to pages or slides.

## Current Limits

- OCR is deferred. Image-only pages report `ocr_skipped` diagnostics.
- Legacy `.ppt` conversion is deferred.
- The SQLite worker queue is single-node.
- Fast mode targets low latency. With Ollama, speed depends on hardware and model settings. With Google Generative AI, speed depends on network latency and API quotas.
