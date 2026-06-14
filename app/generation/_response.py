"""Shared LLM response normalization and provider protocol."""

import json
from typing import Any, Protocol

from app.core.errors import ErrorCode, LLMError


class JSONGenerator(Protocol):
    """Interface that every LLM provider client must implement."""

    async def generate_json(self, prompt: str) -> dict: ...


def normalize_llm_json(raw: str) -> dict[str, Any]:
    """Parse and normalize raw LLM text into the ``{"items": [...]}`` contract.

    Handles markdown code-block stripping, flat-list wrapping, and
    alternative-key search so every provider shares one robust path.
    """
    if not isinstance(raw, str):
        raise LLMError(ErrorCode.LLM_JSON_INVALID, "LLM response did not contain JSON text.")

    clean = _strip_markdown_fences(raw)

    parsed = _parse_json(clean, raw)
    parsed = _normalize_schema(parsed)

    if not isinstance(parsed, dict) or not isinstance(parsed.get("items"), list):
        raise LLMError(ErrorCode.LLM_JSON_INVALID, "LLM JSON did not match expected schema.")
    return parsed


def _strip_markdown_fences(text: str) -> str:
    """Remove wrapping ```json ... ``` blocks that some models add."""
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _parse_json(clean: str, original: str) -> Any:
    """Try parsing cleaned text first, then fall back to the original."""
    try:
        return json.loads(clean)
    except json.JSONDecodeError as exc:
        try:
            return json.loads(original)
        except json.JSONDecodeError:
            raise LLMError(
                ErrorCode.LLM_JSON_INVALID, "LLM returned malformed JSON."
            ) from exc


def _normalize_schema(parsed: Any) -> dict[str, Any]:
    """Coerce common LLM output shapes into ``{"items": [...]}``.``"""
    if isinstance(parsed, list):
        return {"items": parsed}
    if isinstance(parsed, dict) and (
        "items" not in parsed or not isinstance(parsed.get("items"), list)
    ):
        list_keys = [k for k, v in parsed.items() if isinstance(v, list)]
        if list_keys:
            parsed["items"] = parsed[list_keys[0]]
    return parsed
