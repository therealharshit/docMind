from app.schemas.document import FinalDocument, ProcessingMode, Provenance


class EvidenceSnippet:
    def __init__(self, text: str, provenance: Provenance) -> None:
        self.text = text
        self.provenance = provenance


def collect_evidence(document: FinalDocument, mode: ProcessingMode) -> list[EvidenceSnippet]:
    """Build a bounded extractive evidence set for local LLM prompts."""

    max_chars = 18_000 if mode == ProcessingMode.FAST else 60_000
    snippets: list[EvidenceSnippet] = []
    used = 0

    for section in document.sections:
        if not section.body_text:
            continue
        provenance = section.provenance[0] if section.provenance else Provenance(source_type="unknown")
        text = _compact(section.header, section.body_text)
        used = _append(snippets, text, provenance, used, max_chars)
        if used >= max_chars:
            return snippets

    for slide in document.slides:
        text_parts = [slide.title or "", slide.body_text or "", slide.notes or ""]
        text = "\n".join(part for part in text_parts if part.strip())
        if not text:
            continue
        provenance = slide.provenance[0] if slide.provenance else Provenance(source_type="unknown")
        used = _append(snippets, text, provenance, used, max_chars)
        if used >= max_chars:
            return snippets

    return snippets


def render_evidence(snippets: list[EvidenceSnippet]) -> str:
    lines: list[str] = []
    for index, snippet in enumerate(snippets, start=1):
        source = snippet.provenance.source_type
        if snippet.provenance.page_number is not None:
            source += f":page={snippet.provenance.page_number}"
        if snippet.provenance.slide_number is not None:
            source += f":slide={snippet.provenance.slide_number}"
        lines.append(f"[{index}] {source}\n{snippet.text}")
    return "\n\n".join(lines)


def _append(
    snippets: list[EvidenceSnippet],
    text: str,
    provenance: Provenance,
    used: int,
    max_chars: int,
) -> int:
    remaining = max_chars - used
    if remaining <= 0:
        return used
    clipped = text[:remaining].strip()
    if clipped:
        snippets.append(EvidenceSnippet(clipped, provenance))
        used += len(clipped)
    return used


def _compact(header: str | None, body: str) -> str:
    if header:
        return f"{header}\n{body}".strip()
    return body.strip()
