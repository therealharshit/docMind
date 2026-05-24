from app.generation.orchestrator import LocalLLMOrchestrator
from app.schemas.document import (
    DocumentMetadata,
    DocumentType,
    FinalDocument,
    ProcessingMode,
    Provenance,
    Section,
)


class FakeClient:
    async def generate_json(self, prompt: str) -> dict:
        if "glossary" in prompt.lower():
            return {
                "items": [
                    {
                        "term": "Revenue",
                        "definition": "Income from sales.",
                        "evidence_index": 1,
                    }
                ]
            }
        return {
            "items": [
                {
                    "text": "Revenue grew according to the document.",
                    "evidence_index": 1,
                }
            ]
        }


async def test_generation_adds_contract_outputs() -> None:
    document = FinalDocument(
        document_metadata=DocumentMetadata(
            document_id="doc1",
            filename="a.pdf",
            document_type=DocumentType.PDF,
            page_count=1,
            parser="test",
            processing_mode=ProcessingMode.FAST,
        ),
        sections=[
            Section(
                index=1,
                header="Financials",
                body_text="Revenue grew 20 percent.",
                provenance=[Provenance(source_type="pdf_page", page_number=1, confidence=1.0)],
            )
        ],
    )
    from app.core.config import get_settings

    result = await LocalLLMOrchestrator(get_settings(), client=FakeClient()).enrich(document)

    assert result.key_takeaways[0].text
    assert result.glossary[0].term == "Revenue"
    assert result.narration_script[0].provenance[0].page_number == 1
