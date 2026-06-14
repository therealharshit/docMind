"""Factory for building the active LLM client based on configuration."""

from app.core.config import Settings
from app.core.errors import ErrorCode, LLMError
from app.generation._response import JSONGenerator


def build_llm_client(settings: Settings) -> JSONGenerator:
    """Return the correct LLM client for the configured provider.

    Raises :class:`LLMError` when the provider value is unknown or
    required credentials are missing.
    """
    provider = settings.llm_provider

    if provider == "ollama":
        from app.generation.ollama import OllamaClient

        return OllamaClient(settings)

    if provider == "google":
        from app.generation.google_genai import GoogleGenAIClient

        return GoogleGenAIClient(settings)

    raise LLMError(
        ErrorCode.LLM_PROVIDER_INVALID,
        f"Unknown LLM provider: '{provider}'. Use 'ollama' or 'google'.",
        retryable=False,
    )
