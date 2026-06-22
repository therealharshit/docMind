# Repository Guidelines

## Project Structure & Module Organization

Source code lives in `app/`. Route handlers are in `app/api/`, configuration and typed errors in `app/core/`, durable upload/job persistence in `app/storage/`, document parsers in `app/parsers/`, local LLM orchestration in `app/generation/`, and the end-to-end worker flow in `app/pipeline.py` and `app/worker.py`.

Tests live in `tests/` and mirror the runtime modules: parser tests, API tests, storage tests, generation contract tests, and pipeline tests. Deployment files are at the root: `Dockerfile`, `docker-compose.yml`, `.env.example`. Benchmark tooling is in `scripts/`.

## Build, Test, and Development Commands

Create a local environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the API locally:

```bash
uvicorn app.main:app --reload
```

Run quality checks:

```bash
ruff check .
pytest
```

Run Docker services:

```bash
docker compose up --build
docker compose exec ollama ollama pull llama3
```

Run a benchmark:

```bash
python scripts/benchmark.py path/to/document.pdf
```

## Coding Style & Naming Conventions

Use Python 3.11+ with type hints and explicit, boring control flow. Keep modules focused by pipeline stage rather than creating one class per noun. Use 4-space indentation, `snake_case` for functions and variables, `PascalCase` for classes and Pydantic models, and `SCREAMING_SNAKE_CASE` for constants.

`ruff` enforces import ordering and line length. Prefer typed domain exceptions from `app/core/errors.py` over generic exceptions for expected failures.

## Testing Guidelines

Tests use `pytest`, `pytest-asyncio`, and `pytest-cov`. Name test files `test_*.py` and test functions `test_<behavior>()`. Keep LLM tests deterministic by using fake Ollama clients in CI; live Ollama checks belong in benchmarks or explicit local runs. Add tests for both success paths and typed failure states visible through `/status/{document_id}`.

## Commit & Pull Request Guidelines

Use Conventional Commits, matching current history: `feat:`, `fix:`, `test:`, `docs:`, `chore:`. Keep commits incremental and reviewable.

Pull requests should include a short summary, verification commands run, linked issue or TODO when relevant, and notes for changed API contracts, Docker behavior, or performance assumptions.

## Security & Configuration Tips

Never add cloud LLM APIs. This project uses local Ollama only. Do not commit `.env`, uploaded documents, SQLite databases, benchmark outputs, or generated results. Use `.env.example` for documented configuration.
