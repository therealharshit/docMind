import pytest

from app.core.errors import LLMError
from app.generation._response import normalize_llm_json


def test_normalize_valid_json() -> None:
    result = normalize_llm_json('{"items": [{"text": "hello"}]}')
    assert result == {"items": [{"text": "hello"}]}


def test_normalize_markdown_wrapped_json() -> None:
    raw = '```json\n{"items": [{"text": "val"}]}\n```'
    result = normalize_llm_json(raw)
    assert result["items"][0]["text"] == "val"


def test_normalize_flat_list() -> None:
    result = normalize_llm_json('[{"text": "a"}, {"text": "b"}]')
    assert result == {"items": [{"text": "a"}, {"text": "b"}]}


def test_normalize_alternative_key() -> None:
    result = normalize_llm_json('{"takeaways": [{"text": "x"}]}')
    assert result["items"][0]["text"] == "x"


def test_normalize_malformed_json_raises() -> None:
    with pytest.raises(LLMError) as exc_info:
        normalize_llm_json("not valid json at all")
    assert exc_info.value.code == "llm_json_invalid"


def test_normalize_non_string_raises() -> None:
    with pytest.raises(LLMError) as exc_info:
        normalize_llm_json(123)  # type: ignore[arg-type]
    assert exc_info.value.code == "llm_json_invalid"


def test_normalize_no_items_key_raises() -> None:
    with pytest.raises(LLMError) as exc_info:
        normalize_llm_json('{"count": 5}')
    assert exc_info.value.code == "llm_json_invalid"


def test_normalize_markdown_code_block_no_lang() -> None:
    raw = '```\n{"items": [{"text": "bare"}]}\n```'
    result = normalize_llm_json(raw)
    assert result["items"][0]["text"] == "bare"
