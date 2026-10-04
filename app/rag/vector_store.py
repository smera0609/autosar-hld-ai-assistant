from pathlib import Path

import chromadb

from app.models.document import DocumentChunk
from app.rag.embeddings import EmbeddingModel


class HLDVectorStore:
    """
    Persistent ChromaDB vector store for HLD document chunks.
    """

    def __init__(
        self,
        persist_directory: str = "data/vector_store",
        collection_name: str = "autosar_hld",
    ):
        Path(persist_directory).mkdir(
            parents=True,
            exist_ok=True,
        )

        self.embedding_model = EmbeddingModel()

        self.client = chromadb.PersistentClient(
            path=persist_directory
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={
                "description":
                    "AUTOSAR HLD document knowledge base"
            },
        )

    def add_chunks(
        self,
        chunks: list[DocumentChunk],
    ) -> int:

        if not chunks:
            return 0

        documents = []
        ids = []
        metadatas = []

        for chunk in chunks:

            documents.append(chunk.text)
            ids.append(chunk.chunk_id)

            metadatas.append(
                {
                    "filename": chunk.filename,
                    "page_number": chunk.page_number,
                    "section": chunk.section or "",
                    "start_char": chunk.start_char,
                    "end_char": chunk.end_char,
                }
            )

        embeddings = (
            self.embedding_model.encode_documents(documents)
        )

        # upsert prevents duplicate records when a document
        # is indexed again.
        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        return len(chunks)

    def search(
        self,
        query: str,
        top_k: int = 5,
        filename: str | None = None,
    ) -> list[dict]:

        query_embedding = (
            self.embedding_model.encode_query(query)
        )

        query_args = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
            "include": [
                "documents",
                "metadatas",
                "distances",
            ],
        }

        if filename:
            query_args["where"] = {
                "filename": filename
            }

        results = self.collection.query(
            **query_args
        )

        matches = []

        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for chunk_id, document, metadata, distance in zip(
            ids,
            documents,
            metadatas,
            distances,
        ):

            matches.append(
                {
                    "chunk_id": chunk_id,
                    "text": document,
                    "filename": metadata.get(
                        "filename"
                    ),
                    "page_number": metadata.get(
                        "page_number"
                    ),
                    "section": metadata.get(
                        "section"
                    ),
                    "distance": float(distance),
                }
            )

        return matches

    def count(self) -> int:
        return self.collection.count()

    def reset(self):
        """
        Remove the current collection and recreate it.
        Useful during development/testing.
        """

        collection_name = self.collection.name

        self.client.delete_collection(
            collection_name
        )

        self.collection = (
            self.client.get_or_create_collection(
                name=collection_name,
                metadata={
                    "description":
                        "AUTOSAR HLD document knowledge base"
                },
            )
        )