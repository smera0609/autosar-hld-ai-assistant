from app.ingestion.document_processor import (
    DocumentProcessor,
)

from app.rag.vector_store import (
    HLDVectorStore,
)

from app.rag.retriever import (
    HLDRetriever,
)

from app.rag.answer_engine import (
    GroundedAnswerEngine,
)

from app.rag.ollama_provider import (
    OllamaProvider,
)


def main():

    # ---------------------------------
    # 1. SELECT HLD DOCUMENT
    # ---------------------------------

    filename = "Vehicle_Control_HLD_v1.pdf"

    path = (
        "data/sample_hlds/"
        + filename
    )

    # ---------------------------------
    # 2. PROCESS PDF
    # ---------------------------------

    processor = DocumentProcessor()

    processed = processor.process(
        path
    )

    print(
        "\nDocument processed successfully."
    )

    print(
        "Chunks:",
        len(processed["chunks"]),
    )

    # ---------------------------------
    # 3. CREATE VECTOR STORE
    # ---------------------------------

    store = HLDVectorStore(
        persist_directory=(
            "data/rag_test_store"
        ),
        collection_name="rag_test",
    )

    # Clear previous test data
    store.reset()

    # Add HLD chunks to vector DB
    indexed = store.add_chunks(
        processed["chunks"]
    )

    print(
        "Indexed chunks:",
        indexed,
    )

    # ---------------------------------
    # 4. CREATE RETRIEVER
    # ---------------------------------

    retriever = HLDRetriever(
        vector_store=store
    )

    # ---------------------------------
    # 5. CREATE LOCAL LLM
    # ---------------------------------

    llm = OllamaProvider(
        model="qwen3:4b-instruct"
    )

    # ---------------------------------
    # 6. CREATE GROUNDED RAG ENGINE
    # ---------------------------------

    engine = GroundedAnswerEngine(
        retriever=retriever,
        llm_provider=llm,
    )

    # ---------------------------------
    # 7. ASK QUESTION
    # ---------------------------------

    question = (
        "What CAN bus baud rate is configured?"
    )

    answer_result = engine.answer(
        question=question,
        filename=filename,
        top_k=2,
    )

    # ---------------------------------
    # 8. DISPLAY RESULT
    # ---------------------------------

    print(
        "\n=================================="
    )

    print(
        "GROUNDED HLD QUESTION ANSWERING"
    )

    print(
        "=================================="
    )

    print(
        "\nQuestion:"
    )

    print(
        answer_result.question
    )

    print(
        "\nMode:"
    )

    print(
        answer_result.mode
    )

    print(
        "\nAnswer:"
    )

    print(
        answer_result.answer
    )

    # ---------------------------------
    # 9. DISPLAY SOURCE CITATIONS
    # ---------------------------------

    print(
        "\nCITATIONS"
    )

    for citation in answer_result.citations:

        print(
            f"\n[{citation.citation_id}] "
            f"{citation.filename} "
            f"- Page {citation.page_number}"
        )

        print(
            f"Chunk ID: "
            f"{citation.chunk_id}"
        )

        print(
            "\nEvidence:"
        )

        print(
            citation.excerpt
        )

        print(
            "-" * 50
        )

    print(
        "\n=================================="
    )


if __name__ == "__main__":
    main()