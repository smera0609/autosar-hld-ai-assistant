from app.rag.vector_store import HLDVectorStore


class HLDRetriever:
    """
    Retrieves relevant evidence from indexed HLD documents.
    """

    def __init__(
        self,
        vector_store: HLDVectorStore | None = None,
    ):
        self.vector_store = vector_store or HLDVectorStore()

    def retrieve(
        self,
        query: str,
        top_k: int = 4,
        filename: str | None = None,
    ) -> list[dict]:

        if not query.strip():
            raise ValueError("Retrieval query cannot be empty.")

        return self.vector_store.search(
            query=query,
            top_k=top_k,
            filename=filename,
        )