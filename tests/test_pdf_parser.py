from pathlib import Path

from app.ingestion.document_processor import DocumentProcessor


def main():
    file_path = Path("data/sample_hlds/Vehicle_Control_HLD_v1.pdf")

    if not file_path.exists():
        raise FileNotFoundError(
            f"Required test document was not found: {file_path}"
        )

    processor = DocumentProcessor()
    result = processor.process(str(file_path))

    document = result["document"]
    chunks = result["chunks"]

    print("\n==============================")
    print("HLD INGESTION TEST")
    print("==============================")

    print("File:", document.filename)
    print("Pages:", document.page_count)
    print("Extraction:", document.extraction_method)
    print("Total chunks:", len(chunks))

    # Basic verification
    assert document.filename == "Vehicle_Control_HLD_v1.pdf"
    assert document.page_count > 0
    assert len(document.full_text.strip()) > 0
    assert len(chunks) > 0

    if chunks:
        first = chunks[0]

        print("\nFIRST CHUNK")
        print("------------------------------")
        print("Chunk ID:", first.chunk_id)
        print("Page:", first.page_number)
        print("Section:", first.section)

        print("\nText:")
        print(first.text[:500])

    print("\n==============================")
    print("INGESTION PIPELINE SUCCESSFUL")
    print("==============================")


if __name__ == "__main__":
    main()