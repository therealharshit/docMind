import pytest

from app.core.errors import LLMError
from app.generation.factory import build_llm_client
from app.generation.ollama import OllamaClient


def test_factory_returns_ollama_by_default(temp_env) -> None:
    from app.core.config import get_settings

    settings = get_settings()
    client = build_llm_client(settings)
    assert isinstance(client, OllamaClient)


def test_factory_returns_ollama_explicitly(monkeypatch, temp_env) -> None:
    from app.core.config import get_settings

    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    get_settings.cache_clear()

    settings = get_settings()
    client = build_llm_client(settings)
    assert isinstance(client, OllamaClient)


def test_factory_raises_for_google_without_key(monkeypatch, temp_env) -> None:
    from app.core.config import get_settings

    monkeypatch.setenv("LLM_PROVIDER", "google")
    monkeypatch.setenv("GOOGLE_API_KEY", "")
    get_settings.cache_clear()

    settings = get_settings()
    with pytest.raises(LLMError) as exc_info:
        build_llm_client(settings)
    assert exc_info.value.code == "llm_provider_invalid"
