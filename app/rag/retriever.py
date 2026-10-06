import re

from app.rag.vector_store import HLDVectorStore


class HLDRetriever:
    """
    Retrieves and reranks relevant evidence from indexed HLD documents.

    Strategy:
    1. Retrieve a larger semantic candidate set from Chroma.
    2. Calculate lexical overlap with the user question.
    3. Combine semantic distance and lexical evidence.
    4. Remove near-duplicate chunks.
    5. Return the best evidence chunks.

    This makes retrieval more robust for large HLD documents where
    hundreds or thousands of chunks may be indexed.
    """

    def __init__(
        self,
        vector_store: HLDVectorStore | None = None,
    ):
        self.vector_store = vector_store or HLDVectorStore()

    @staticmethod
    def _tokens(text: str) -> set[str]:
        """
        Convert text into normalized searchable tokens.
        """

        return {
            token.lower()
            for token in re.findall(
                r"[A-Za-z][A-Za-z0-9_-]+",
                text,
            )
            if len(token) > 2
        }

    @classmethod
    def _lexical_score(
        cls,
        query: str,
        text: str,
    ) -> float:
        """
        Measures how many meaningful query terms occur
        in a candidate evidence chunk.
        """

        query_tokens = cls._tokens(query)

        if not query_tokens:
            return 0.0

        text_tokens = cls._tokens(text)

        matches = query_tokens.intersection(
            text_tokens
        )

        return len(matches) / len(query_tokens)

    @staticmethod
    def _semantic_score(distance: float) -> float:
        """
        Convert Chroma distance into a simple bounded
        relevance score.

        This is a ranking score only. It must NOT be
        presented as model confidence.
        """

        distance = max(float(distance), 0.0)

        return 1.0 / (1.0 + distance)

    @staticmethod
    def _normalize_text(text: str) -> str:
        return " ".join(
            text.lower().split()
        )

    def retrieve(
        self,
        query: str,
        top_k: int = 4,
        filename: str | None = None,
    ) -> list[dict]:

        if not query.strip():
            raise ValueError(
                "Retrieval query cannot be empty."
            )

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than 0."
            )

        # Retrieve more candidates than we finally need.
        # This is particularly useful for long documents.
        candidate_k = max(
            top_k * 4,
            12,
        )

        candidates = self.vector_store.search(
            query=query,
            top_k=candidate_k,
            filename=filename,
        )

        if not candidates:
            return []

        reranked = []

        for item in candidates:

            semantic_score = self._semantic_score(
                item.get(
                    "distance",
                    1.0,
                )
            )

            lexical_score = self._lexical_score(
                query,
                item.get(
                    "text",
                    "",
                ),
            )

            # Semantic meaning is the primary signal.
            # Lexical overlap helps distinguish highly
            # similar architecture descriptions.
            combined_score = (
                0.75 * semantic_score
                + 0.25 * lexical_score
            )

            enriched = dict(item)

            enriched[
                "semantic_score"
            ] = semantic_score

            enriched[
                "lexical_score"
            ] = lexical_score

            enriched[
                "retrieval_score"
            ] = combined_score

            reranked.append(enriched)

        reranked.sort(
            key=lambda item: item[
                "retrieval_score"
            ],
            reverse=True,
        )

        # Remove highly repetitive evidence.
        # Long engineering documents frequently repeat
        # architecture descriptions across sections.
        selected = []
        seen_text = set()

        for item in reranked:

            normalized = self._normalize_text(
                item["text"]
            )

            # Exact normalized duplicates are skipped.
            if normalized in seen_text:
                continue

            seen_text.add(normalized)

            selected.append(item)

            if len(selected) >= top_k:
                break

        return selected