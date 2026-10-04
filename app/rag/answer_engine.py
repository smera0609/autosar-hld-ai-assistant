from dataclasses import dataclass, field

from app.rag.retriever import HLDRetriever
from app.rag.prompts import build_prompt


@dataclass
class Citation:
    citation_id: int
    filename: str
    page_number: int
    chunk_id: str
    excerpt: str


@dataclass
class GroundedAnswer:
    question: str
    answer: str
    citations: list[Citation] = field(
        default_factory=list
    )
    mode: str = "evidence"
    prompt: str = ""


class GroundedAnswerEngine:
    """
    Retrieval-grounded Q&A engine.

    Evidence mode works without an LLM.
    An LLM provider can be attached later.
    """

    def __init__(
        self,
        retriever: HLDRetriever,
        llm_provider=None,
    ):
        self.retriever = retriever
        self.llm_provider = llm_provider

    def answer(
        self,
        question: str,
        filename: str | None = None,
        top_k: int = 3,
    ) -> GroundedAnswer:

        if not question.strip():
            raise ValueError(
                "Question cannot be empty."
            )

        evidence = self.retriever.retrieve(
            query=question,
            top_k=top_k,
            filename=filename,
        )

        citations = self._citations(
            evidence
        )

        prompt = build_prompt(
            question,
            evidence,
        )

        if not evidence:

            return GroundedAnswer(
                question=question,
                answer=(
                    "Insufficient document evidence "
                    "was retrieved to answer this question."
                ),
                citations=[],
                mode="evidence",
                prompt=prompt,
            )

        if self.llm_provider is not None:

            answer_text = (
                self.llm_provider.generate(
                    prompt
                )
            )

            mode = "llm-rag"

        else:

            answer_text = (
                "Relevant evidence was retrieved "
                "from the HLD. Review the cited "
                "source excerpts below."
            )

            mode = "evidence"

        return GroundedAnswer(
            question=question,
            answer=answer_text,
            citations=citations,
            mode=mode,
            prompt=prompt,
        )

    @staticmethod
    def _citations(
        evidence: list[dict],
    ) -> list[Citation]:

        citations = []

        for index, item in enumerate(
            evidence,
            start=1,
        ):

            text = item["text"].strip()

            excerpt = (
                text[:500] + "..."
                if len(text) > 500
                else text
            )

            citations.append(
                Citation(
                    citation_id=index,
                    filename=item["filename"],
                    page_number=item[
                        "page_number"
                    ],
                    chunk_id=item[
                        "chunk_id"
                    ],
                    excerpt=excerpt,
                )
            )

        return citations