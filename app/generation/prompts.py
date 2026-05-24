SYSTEM_CONTRACT = (
    "You are a local document analysis engine. Use only the provided evidence. "
    "Do not invent facts. Return valid JSON only, with no markdown."
)


def takeaways_prompt(evidence: str) -> str:
    return f"""{SYSTEM_CONTRACT}

Task: Generate 5-8 concise key takeaways from the evidence.
Output JSON schema:
{{"items":[{{"text":"takeaway grounded in evidence","evidence_index":1}}]}}
Rules:
- Use only evidence below.
- If evidence is thin, return fewer items.
- evidence_index must reference the most relevant evidence block number.

Evidence:
{evidence}
"""


def glossary_prompt(evidence: str) -> str:
    return f"""{SYSTEM_CONTRACT}

Task: Generate a glossary of important domain terms from the evidence.
Output JSON schema:
{{"items":[{{"term":"term","definition":"definition grounded in evidence","evidence_index":1}}]}}
Rules:
- Include only terms present in the evidence.
- Keep definitions short and factual.
- evidence_index must reference the most relevant evidence block number.

Evidence:
{evidence}
"""


def narration_prompt(evidence: str) -> str:
    return f"""{SYSTEM_CONTRACT}

Task: Generate a narration script suitable for explaining this document.
Output JSON schema:
{{"items":[{{"text":"spoken narration segment","evidence_index":1}}]}}
Rules:
- Keep each segment under 90 words.
- Use only evidence below.
- evidence_index must reference the most relevant evidence block number.

Evidence:
{evidence}
"""
