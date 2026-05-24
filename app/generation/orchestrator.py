import asyncio
from typing import Protocol

from app.core.config import Settings
from app.generation.chunking import EvidenceSnippet, collect_evidence, render_evidence
from app.generation.ollama import OllamaClient
from app.generation.prompts import glossary_prompt, narration_prompt, takeaways_prompt
from app.schemas.document import FinalDocument, GeneratedItem, GlossaryItem, Provenance


class JSONGenerator(Protocol):
    async def generate_json(self, prompt: str) -> dict:
        ...


class LocalLLMOrchestrator:
    """Runs bounded local LLM calls and composes generated document fields."""

    def __init__(self, settings: Settings, client: JSONGenerator | None = None) -> None:
        self.settings = settings
        self.client = client or OllamaClient(settings)

    async def enrich(self, document: FinalDocument) -> FinalDocument:
        mode = document.document_metadata.processing_mode
        snippets = collect_evidence(document, mode)
        document.document_metadata.diagnostics["evidence_snippet_count"] = len(snippets)
        if not snippets:
            return document

        evidence = render_evidence(snippets)
        takeaways, glossary, narration = await asyncio.gather(
            self.client.generate_json(takeaways_prompt(evidence)),
            self.client.generate_json(glossary_prompt(evidence)),
            self.client.generate_json(narration_prompt(evidence)),
        )
        document.key_takeaways = self._generated_items(takeaways, snippets)
        document.glossary = self._glossary_items(glossary, snippets)
        document.narration_script = self._generated_items(narration, snippets)
        return document

    def _generated_items(self, payload: dict, snippets: list[EvidenceSnippet]) -> list[GeneratedItem]:
        items: list[GeneratedItem] = []
        for raw in payload.get("items", []):
            text = str(raw.get("text", "")).strip()
            if not text:
                continue
            items.append(GeneratedItem(text=text, provenance=[self._provenance(raw, snippets)]))
        return items

    def _glossary_items(self, payload: dict, snippets: list[EvidenceSnippet]) -> list[GlossaryItem]:
        items: list[GlossaryItem] = []
        for raw in payload.get("items", []):
            term = str(raw.get("term", "")).strip()
            definition = str(raw.get("definition", "")).strip()
            if not term or not definition:
                continue
            items.append(
                GlossaryItem(term=term, definition=definition, provenance=[self._provenance(raw, snippets)])
            )
        return items

    def _provenance(self, raw: dict, snippets: list[EvidenceSnippet]) -> Provenance:
        try:
            index = int(raw.get("evidence_index", 1)) - 1
        except (TypeError, ValueError):
            index = 0
        if 0 <= index < len(snippets):
            return snippets[index].provenance
        return snippets[0].provenance
