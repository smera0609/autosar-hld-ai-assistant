from app.extraction.pdf_architecture_extractor import (
    PDFArchitectureExtractor,
)

from app.comparison.revision_comparator import (
    RevisionComparator,
)


def main():

    extractor = PDFArchitectureExtractor()
    comparator = RevisionComparator()

    old = extractor.extract(
        "data/sample_hlds/"
        "Vehicle_Control_HLD_v1.pdf"
    )

    new = extractor.extract(
        "data/sample_hlds/"
        "Vehicle_Control_HLD_v2.pdf"
    )

    comparison = comparator.compare(
        old,
        new,
    )

    print(
        "\n=================================="
    )
    print(
        "HLD REVISION COMPARISON"
    )
    print(
        "=================================="
    )

    print(
        f"Old: {comparison.old_file} "
        f"(v{comparison.old_version})"
    )

    print(
        f"New: {comparison.new_file} "
        f"(v{comparison.new_version})"
    )

    print(
        f"\nTotal changes: "
        f"{comparison.total_changes}"
    )

    print(
        "\nDETECTED CHANGES"
    )

    for index, change in enumerate(
        comparison.changes,
        start=1,
    ):

        print(
            f"\n{index}. "
            f"[{change.category}] "
            f"{change.change_type}"
        )

        print(
            f"   {change.description}"
        )

    print(
        "\n=================================="
    )


if __name__ == "__main__":
    main()