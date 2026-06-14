"""Google Generative AI client implementing the JSONGenerator protocol."""

import asyncio
from typing import Any

from app.core.config import Settings
from app.core.errors import ErrorCode, LLMError
from app.generation._response import normalize_llm_json


class GoogleGenAIClient:
    """Async client for Google Generative AI (Gemini) with JSON mode."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        if not settings.google_api_key:
            raise LLMError(
                ErrorCode.LLM_PROVIDER_INVALID,
                "GOOGLE_API_KEY is required when LLM_PROVIDER is 'google'.",
                retryable=False,
            )
        try:
            from google import generativeai as genai
        except ImportError as exc:
            raise LLMError(
                ErrorCode.LLM_PROVIDER_INVALID,
                "google-generativeai package is not installed. "
                "Run: pip install google-generativeai",
                retryable=False,
            ) from exc

        genai.configure(api_key=settings.google_api_key)
        self._model = genai.GenerativeModel(
            model_name=settings.google_model,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )

    async def generate_json(self, prompt: str) -> dict[str, Any]:
        """Send a prompt to Gemini and return normalized JSON."""
        try:
            response = await asyncio.to_thread(
                self._model.generate_content, prompt
            )
        except Exception as exc:
            error_name = type(exc).__name__
            if "timeout" in error_name.lower() or "deadline" in error_name.lower():
                raise LLMError(
                    ErrorCode.GOOGLE_TIMEOUT,
                    f"Google GenAI request timed out: {exc}",
                    retryable=True,
                ) from exc
            raise LLMError(
                ErrorCode.GOOGLE_API_ERROR,
                f"Google GenAI API error: {exc}",
                retryable=True,
            ) from exc

        raw = response.text
        if not raw:
            raise LLMError(
                ErrorCode.LLM_JSON_INVALID,
                "Google GenAI returned an empty response.",
            )

        return normalize_llm_json(raw)
