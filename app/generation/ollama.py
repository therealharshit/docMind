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
        # Dynamically set context window based on pipeline mode to avoid model truncation
        num_ctx = 8192 if self.settings.pipeline_mode == "fast" else 24576
        payload = {
            "model": self.settings.ollama_model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1,
                "num_ctx": num_ctx,
            },
        }
        timeout = httpx.Timeout(self.settings.ollama_timeout_seconds)
        try:
            async with httpx.AsyncClient(
                base_url=self.settings.ollama_base_url,
                timeout=timeout,
            ) as client:
                response = await client.post("/api/generate", json=payload)
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise LLMError(
                ErrorCode.OLLAMA_TIMEOUT,
                "Ollama request timed out.",
                retryable=True,
            ) from exc
        except httpx.HTTPError as exc:
            raise LLMError(
                ErrorCode.OLLAMA_UNAVAILABLE,
                "Ollama is unavailable.",
                retryable=True,
            ) from exc

        body = response.json()
        raw = body.get("response")
        if not isinstance(raw, str):
            raise LLMError(ErrorCode.LLM_JSON_INVALID, "Ollama response did not contain JSON text.")

        # Clean markdown code blocks if the local LLM wrapped the JSON
        clean_raw = raw.strip()
        if clean_raw.startswith("```"):
            lines = clean_raw.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            clean_raw = "\n".join(lines).strip()

        try:
            parsed = json.loads(clean_raw)
        except json.JSONDecodeError as exc:
            # Fallback to loading the original raw response
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                raise LLMError(ErrorCode.LLM_JSON_INVALID, "Ollama returned malformed JSON.") from exc

        # Resilient normalization of output schemas
        if isinstance(parsed, list):
            # Wrap flat arrays into the expected dictionary shape
            parsed = {"items": parsed}
        elif isinstance(parsed, dict):
            if "items" not in parsed or not isinstance(parsed["items"], list):
                # Search for another key whose value is a list of elements
                list_keys = [k for k, v in parsed.items() if isinstance(v, list)]
                if list_keys:
                    parsed["items"] = parsed[list_keys[0]]

        if not isinstance(parsed, dict) or not isinstance(parsed.get("items"), list):
            raise LLMError(ErrorCode.LLM_JSON_INVALID, "Ollama JSON did not match expected schema.")
        return parsed

