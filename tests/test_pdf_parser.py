from app.ingestion.document_processor import DocumentProcessor


def main():

    file_path = "data/sample_hlds/test_hld.pdf"

    processor = DocumentProcessor()

    try:
        result = processor.process(file_path)

    except FileNotFoundError:
        print(
            "\nTEST PDF NOT FOUND\n"
            "Place test_hld.pdf inside data/sample_hlds/"
        )
        return

    document = result["document"]
    chunks = result["chunks"]

    print("\n==============================")
    print("HLD INGESTION TEST")
    print("==============================")

    print("File:", document.filename)
    print("Pages:", document.page_count)
    print("Extraction:", document.extraction_method)

    print("\nTotal chunks:", len(chunks))

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