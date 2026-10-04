from app.ingestion.document_processor import (
    DocumentProcessor,
)

from app.rag.vector_store import HLDVectorStore
from app.rag.retriever import HLDRetriever


DOCUMENTS = [
    "Vehicle_Control_HLD_v1.pdf",
    "Vehicle_Control_HLD_v2.pdf",
    "Braking_System_HLD.pdf",
    "Door_Control_HLD.pdf",
    "Body_Control_HLD.pdf",
]


def main():

    processor = DocumentProcessor()

    store = HLDVectorStore(
        persist_directory="data/test_vector_store",
        collection_name="test_hld",
    )

    # Start with a clean test collection.
    store.reset()

    print("\n==============================")
    print("INDEXING HLD DOCUMENTS")
    print("==============================")

    total = 0

    for filename in DOCUMENTS:

        path = f"data/sample_hlds/{filename}"

        result = processor.process(path)

        count = store.add_chunks(
            result["chunks"]
        )

        total += count

        print(
            f"{filename}: {count} chunks"
        )

    print("\nIndexed chunks:", total)
    print("Vector DB count:", store.count())

    retriever = HLDRetriever(store)

    query = (
        "Which component processes "
        "wheel speed information?"
    )

    print("\n==============================")
    print("QUERY")
    print("==============================")

    print(query)

    results = retriever.retrieve(
        query=query,
        top_k=3,
        filename="Vehicle_Control_HLD_v1.pdf",
    )

    print("\n==============================")
    print("RETRIEVED EVIDENCE")
    print("==============================")

    for index, result in enumerate(
        results,
        start=1,
    ):

        print(
            f"\nResult {index}"
        )

        print(
            "Source:",
            result["filename"],
        )

        print(
            "Page:",
            result["page_number"],
        )

        print(
            "Distance:",
            round(
                result["distance"],
                4,
            ),
        )

        print("\nEvidence:")

        print(
            result["text"][:600]
        )

        print("-" * 60)


if __name__ == "__main__":
    main()