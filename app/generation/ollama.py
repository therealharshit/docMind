import json
from typing import Any

import httpx

from app.core.config import Settings
from app.core.errors import ErrorCode, LLMError


class OllamaClient:
    """Small async client for Ollama's local generate API."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def generate_json(self, prompt: str) -> dict[str, Any]:
        payload = {
            "model": self.settings.ollama_model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1},
        }
        timeout = httpx.Timeout(self.settings.ollama_timeout_seconds)
        try:
            async with httpx.AsyncClient(base_url=self.settings.ollama_base_url, timeout=timeout) as client:
                response = await client.post("/api/generate", json=payload)
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise LLMError(ErrorCode.OLLAMA_TIMEOUT, "Ollama request timed out.", retryable=True) from exc
        except httpx.HTTPError as exc:
            raise LLMError(ErrorCode.OLLAMA_UNAVAILABLE, "Ollama is unavailable.", retryable=True) from exc

        body = response.json()
        raw = body.get("response")
        if not isinstance(raw, str):
            raise LLMError(ErrorCode.LLM_JSON_INVALID, "Ollama response did not contain JSON text.")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LLMError(ErrorCode.LLM_JSON_INVALID, "Ollama returned malformed JSON.") from exc
        if not isinstance(parsed, dict) or not isinstance(parsed.get("items"), list):
            raise LLMError(ErrorCode.LLM_JSON_INVALID, "Ollama JSON did not match expected schema.")
        return parsed
