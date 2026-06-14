import pytest

from app.core.errors import LLMError
from app.generation.google_genai import GoogleGenAIClient


class FakeGenerativeModel:
    """Minimal stand-in for google.generativeai.GenerativeModel."""

    def __init__(self, response_text: str) -> None:
        self._response_text = response_text

    def generate_content(self, prompt: str):  # noqa: ANN201
        class _Response:
            def __init__(self, text: str) -> None:
                self.text = text

        return _Response(self._response_text)


class FakeFailingModel:
    """Model that raises an API error."""

    def generate_content(self, prompt: str):  # noqa: ANN201
        raise RuntimeError("Quota exceeded")


async def test_google_genai_client_returns_parsed_json(monkeypatch, temp_env) -> None:
    from app.core.config import get_settings

    monkeypatch.setenv("LLM_PROVIDER", "google")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-123")
    get_settings.cache_clear()

    settings = get_settings()

    # Bypass the real SDK import and configuration in __init__
    client = object.__new__(GoogleGenAIClient)
    client.settings = settings
    client._model = FakeGenerativeModel('{"items": [{"text": "insight"}]}')

    result = await client.generate_json("test prompt")
    assert result["items"][0]["text"] == "insight"


async def test_google_genai_client_handles_api_error(monkeypatch, temp_env) -> None:
    from app.core.config import get_settings

    monkeypatch.setenv("LLM_PROVIDER", "google")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-123")
    get_settings.cache_clear()

    settings = get_settings()

    client = object.__new__(GoogleGenAIClient)
    client.settings = settings
    client._model = FakeFailingModel()

    with pytest.raises(LLMError) as exc_info:
        await client.generate_json("test prompt")
    assert exc_info.value.code == "google_api_error"
    assert exc_info.value.retryable is True


async def test_google_genai_client_handles_empty_response(monkeypatch, temp_env) -> None:
    from app.core.config import get_settings

    monkeypatch.setenv("LLM_PROVIDER", "google")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-123")
    get_settings.cache_clear()

    settings = get_settings()

    client = object.__new__(GoogleGenAIClient)
    client.settings = settings
    client._model = FakeGenerativeModel("")

    with pytest.raises(LLMError) as exc_info:
        await client.generate_json("test prompt")
    assert exc_info.value.code == "llm_json_invalid"


async def test_google_genai_client_requires_api_key(monkeypatch, temp_env) -> None:
    from app.core.config import get_settings

    monkeypatch.setenv("LLM_PROVIDER", "google")
    monkeypatch.setenv("GOOGLE_API_KEY", "")
    get_settings.cache_clear()

    settings = get_settings()
    with pytest.raises(LLMError) as exc_info:
        GoogleGenAIClient(settings)
    assert exc_info.value.code == "llm_provider_invalid"
