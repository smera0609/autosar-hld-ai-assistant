SYSTEM_PROMPT = """
You are an AUTOSAR High Level Design document analysis assistant.

Answer the question using ONLY the supplied HLD evidence.

RULES:
- Do not use outside knowledge.
- Do not invent information.
- Preserve component, interface, port and signal names exactly.
- Do not show analysis or reasoning.
- Do not explain how you found the answer.
- Return ONLY the final answer.
- Maximum 2 sentences.
- If the answer is not explicitly supported by the evidence,
  return exactly:
  Insufficient evidence in the provided HLD.
"""


def build_prompt(
    question: str,
    evidence: list[dict],
) -> str:

    blocks = []

    for index, item in enumerate(
        evidence,
        start=1,
    ):
        blocks.append(
            f"""
SOURCE {index}
Document: {item['filename']}
Page: {item['page_number']}

{item['text']}
""".strip()
        )

    context = "\n\n".join(blocks)

    return f"""
{SYSTEM_PROMPT}

HLD EVIDENCE:
{context}

QUESTION:
{question}

Return ONLY the final answer.
Do not include reasoning.

/no_think

FINAL ANSWER:
""".strip()