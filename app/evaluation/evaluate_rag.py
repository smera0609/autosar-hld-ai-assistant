from pathlib import Path

from app.ingestion.document_processor import DocumentProcessor
from app.rag.vector_store import HLDVectorStore
from app.rag.retriever import HLDRetriever
from app.rag.answer_engine import GroundedAnswerEngine
from app.rag.ollama_provider import OllamaProvider


# =========================================================
# CONFIGURATION
# =========================================================

FILENAME = "Vehicle_Control_HLD_v1.pdf"

PDF_PATH = Path(
    "data/sample_hlds"
) / FILENAME

VECTOR_DIRECTORY = (
    "data/rag_evaluation_store"
)

COLLECTION_NAME = (
    "rag_evaluation"
)

MODEL_NAME = (
    "qwen3:4b-instruct"
)

INSUFFICIENT_TEXT = (
    "insufficient evidence "
    "in the provided hld"
)


# =========================================================
# BENCHMARK
# =========================================================

TEST_CASES = [

    # -----------------------------------------------------
    # SUPPORTED QUESTIONS
    # -----------------------------------------------------

    {
        "id": "Q1",
        "question": (
            "Which component processes "
            "wheel speed information?"
        ),
        "supported": True,
        "expected_keywords": [
            "VehicleSpeedController",
        ],
    },

    {
        "id": "Q2",
        "question": (
            "Which component provides "
            "WheelSpeedInterface?"
        ),
        "supported": True,
        "expected_keywords": [
            "WheelSpeedSensor",
        ],
    },

    {
        "id": "Q3",
        "question": (
            "Which component consumes "
            "VehicleSpeedInterface?"
        ),
        "supported": True,
        "expected_keywords": [
            "InstrumentCluster",
        ],
    },

    {
        "id": "Q4",
        "question": (
            "What unit is used for "
            "the WheelSpeed signal?"
        ),
        "supported": True,
        "expected_keywords": [
            "km/h",
        ],
    },

    {
        "id": "Q5",
        "question": (
            "Which component does "
            "InstrumentCluster depend on?"
        ),
        "supported": True,
        "expected_keywords": [
            "VehicleSpeedController",
        ],
    },

    {
        "id": "Q6",
        "question": (
            "What is the document ID?"
        ),
        "supported": True,
        "expected_keywords": [
            "HLD-VCS-001",
        ],
    },

    # -----------------------------------------------------
    # UNSUPPORTED QUESTIONS
    # -----------------------------------------------------

    {
        "id": "Q7",
        "question": (
            "What CAN bus baud rate "
            "is configured?"
        ),
        "supported": False,
        "expected_keywords": [],
    },

    {
        "id": "Q8",
        "question": (
            "What microcontroller model "
            "is used in the system?"
        ),
        "supported": False,
        "expected_keywords": [],
    },

    {
        "id": "Q9",
        "question": (
            "What operating system "
            "does the ECU use?"
        ),
        "supported": False,
        "expected_keywords": [],
    },

    {
        "id": "Q10",
        "question": (
            "What is the CAN message "
            "identifier for WheelSpeed?"
        ),
        "supported": False,
        "expected_keywords": [],
    },
]


# =========================================================
# HELPERS
# =========================================================

def normalize(value):
    return str(value).strip().lower()


def contains_expected_keyword(
    answer,
    keywords,
):
    """
    For supported benchmark questions, the answer
    must contain every expected keyword.

    These benchmark answers are intentionally simple
    and deterministic.
    """

    normalized_answer = normalize(
        answer
    )

    return all(
        normalize(keyword)
        in normalized_answer
        for keyword in keywords
    )


def is_refusal(answer):
    """
    Check whether the RAG system correctly states
    that the HLD does not contain enough evidence.
    """

    normalized_answer = normalize(
        answer
    )

    return (
        INSUFFICIENT_TEXT
        in normalized_answer
    )


def citations_are_valid(
    citations,
):
    """
    Validate citation metadata.

    A valid citation must point to the selected
    document, contain a page number, chunk ID,
    and non-empty evidence excerpt.
    """

    if not citations:
        return False

    for citation in citations:

        if (
            citation.filename
            != FILENAME
        ):
            return False

        if (
            citation.page_number
            is None
        ):
            return False

        if not str(
            citation.chunk_id
        ).strip():
            return False

        if not str(
            citation.excerpt
        ).strip():
            return False

    return True


# =========================================================
# MAIN
# =========================================================

def main():

    print("=" * 78)

    print(
        "AUTOSAR HLD ASSISTANT - "
        "RAG QUESTION ANSWERING EVALUATION"
    )

    print("=" * 78)

    if not PDF_PATH.exists():

        raise FileNotFoundError(
            f"HLD not found: {PDF_PATH}"
        )

    # -----------------------------------------------------
    # PROCESS DOCUMENT
    # -----------------------------------------------------

    processor = (
        DocumentProcessor()
    )

    processed = processor.process(
        str(PDF_PATH)
    )

    chunks = processed[
        "chunks"
    ]

    print(
        f"\nDocument: {FILENAME}"
    )

    print(
        f"Chunks: {len(chunks)}"
    )

    # -----------------------------------------------------
    # VECTOR STORE
    # -----------------------------------------------------

    store = HLDVectorStore(
        persist_directory=(
            VECTOR_DIRECTORY
        ),
        collection_name=(
            COLLECTION_NAME
        ),
    )

    store.reset()

    indexed = store.add_chunks(
        chunks
    )

    print(
        f"Indexed chunks: {indexed}"
    )

    # -----------------------------------------------------
    # RAG ENGINE
    # -----------------------------------------------------

    retriever = HLDRetriever(
        vector_store=store
    )

    llm = OllamaProvider(
        model=MODEL_NAME
    )

    engine = GroundedAnswerEngine(
        retriever=retriever,
        llm_provider=llm,
    )

    # -----------------------------------------------------
    # COUNTERS
    # -----------------------------------------------------

    supported_total = 0
    supported_correct = 0

    unsupported_total = 0
    unsupported_correct = 0

    supported_with_citations = 0
    supported_valid_citations = 0

    total_questions = len(
        TEST_CASES
    )

    total_correct = 0

    # -----------------------------------------------------
    # RUN BENCHMARK
    # -----------------------------------------------------

    for test in TEST_CASES:

        print(
            "\n"
            + "-" * 78
        )

        print(
            f"{test['id']}: "
            f"{test['question']}"
        )

        print(
            "-" * 78
        )

        result = engine.answer(
            question=test[
                "question"
            ],
            filename=FILENAME,
            top_k=2,
        )

        answer = (
            result.answer
        )

        citations = (
            result.citations
        )

        print(
            f"Mode: {result.mode}"
        )

        print(
            f"Answer: {answer}"
        )

        print(
            "Citation count: "
            f"{len(citations)}"
        )

        # =================================================
        # SUPPORTED QUESTION
        # =================================================

        if test["supported"]:

            supported_total += 1

            answer_correct = (
                contains_expected_keyword(
                    answer,
                    test[
                        "expected_keywords"
                    ],
                )
                and not is_refusal(
                    answer
                )
            )

            has_citations = (
                len(citations) > 0
            )

            valid_citations = (
                citations_are_valid(
                    citations
                )
            )

            if answer_correct:
                supported_correct += 1
                total_correct += 1

            if has_citations:
                supported_with_citations += 1

            if valid_citations:
                supported_valid_citations += 1

            print(
                "Expected keywords: "
                + ", ".join(
                    test[
                        "expected_keywords"
                    ]
                )
            )

            print(
                "Answer correct: "
                f"{answer_correct}"
            )

            print(
                "Citation present: "
                f"{has_citations}"
            )

            print(
                "Citation metadata valid: "
                f"{valid_citations}"
            )

        # =================================================
        # UNSUPPORTED QUESTION
        # =================================================

        else:

            unsupported_total += 1

            refused = is_refusal(
                answer
            )

            if refused:
                unsupported_correct += 1
                total_correct += 1

            print(
                "Expected behavior: "
                "REFUSE / INSUFFICIENT EVIDENCE"
            )

            print(
                "Correct refusal: "
                f"{refused}"
            )

    # =====================================================
    # FINAL METRICS
    # =====================================================

    supported_accuracy = (
        supported_correct
        / supported_total
        if supported_total
        else 0.0
    )

    refusal_accuracy = (
        unsupported_correct
        / unsupported_total
        if unsupported_total
        else 0.0
    )

    citation_coverage = (
        supported_with_citations
        / supported_total
        if supported_total
        else 0.0
    )

    citation_validity = (
        supported_valid_citations
        / supported_total
        if supported_total
        else 0.0
    )

    overall_accuracy = (
        total_correct
        / total_questions
        if total_questions
        else 0.0
    )

    print(
        "\n"
        + "=" * 78
    )

    print(
        "RAG EVALUATION RESULTS"
    )

    print(
        "=" * 78
    )

    print(
        "Supported answer correctness : "
        f"{supported_correct}/"
        f"{supported_total} "
        f"({supported_accuracy:.3f})"
    )

    print(
        "Unsupported refusal accuracy : "
        f"{unsupported_correct}/"
        f"{unsupported_total} "
        f"({refusal_accuracy:.3f})"
    )

    print(
        "Supported citation coverage  : "
        f"{supported_with_citations}/"
        f"{supported_total} "
        f"({citation_coverage:.3f})"
    )

    print(
        "Citation metadata validity   : "
        f"{supported_valid_citations}/"
        f"{supported_total} "
        f"({citation_validity:.3f})"
    )

    print(
        "Overall benchmark correctness: "
        f"{total_correct}/"
        f"{total_questions} "
        f"({overall_accuracy:.3f})"
    )

    print(
        "\nIMPORTANT:"
    )

    print(
        "Answer correctness here uses "
        "predefined expected keywords for "
        "the controlled benchmark."
    )

    print(
        "Citation validity verifies source "
        "metadata and evidence presence; it "
        "does not independently prove that "
        "every generated statement is "
        "entailed by the cited text."
    )

    print(
        "\nRAG EVALUATION COMPLETE"
    )


if __name__ == "__main__":
    main()