import json

from app.extraction.pdf_architecture_extractor import (
    PDFArchitectureExtractor,
)

from app.validation.consistency_checker import (
    ConsistencyChecker,
)


DOCUMENTS = [
    "Vehicle_Control_HLD_v1.pdf",
    "Vehicle_Control_HLD_v2.pdf",
    "Braking_System_HLD.pdf",
    "Door_Control_HLD.pdf",
    "Body_Control_HLD.pdf",
]


def names(items):
    return {
        item.name
        for item in items
    }


def precision_recall(
    predicted,
    expected,
):

    predicted = set(predicted)
    expected = set(expected)

    true_positive = len(
        predicted & expected
    )

    precision = (
        true_positive / len(predicted)
        if predicted
        else 0.0
    )

    recall = (
        true_positive / len(expected)
        if expected
        else 0.0
    )

    return precision, recall


def main():

    extractor = PDFArchitectureExtractor()
    checker = ConsistencyChecker()

    with open(
        "data/ground_truth/"
        "architecture_ground_truth.json",
        "r",
        encoding="utf-8",
    ) as file:

        ground_truth = json.load(file)[
            "documents"
        ]

    print(
        "\n=================================="
    )

    print(
        "REAL PDF ARCHITECTURE EXTRACTION"
    )

    print(
        "=================================="
    )

    for filename in DOCUMENTS:

        path = (
            f"data/sample_hlds/{filename}"
        )

        architecture = extractor.extract(
            path
        )

        expected = ground_truth[
            filename
        ]

        expected_components = {
            item["name"]
            for item
            in expected["components"]
        }

        expected_interfaces = {
            item["name"]
            for item
            in expected["interfaces"]
        }

        component_precision, component_recall = (
            precision_recall(
                names(
                    architecture.components
                ),
                expected_components,
            )
        )

        interface_precision, interface_recall = (
            precision_recall(
                names(
                    architecture.interfaces
                ),
                expected_interfaces,
            )
        )

        issues = checker.validate(
            architecture
        )

        print(
            f"\nDOCUMENT: {filename}"
        )

        print(
            "Document ID:",
            architecture.document_id,
        )

        print(
            "Version:",
            architecture.version,
        )

        print(
            "Components extracted:",
            len(
                architecture.components
            ),
        )

        print(
            "Interfaces extracted:",
            len(
                architecture.interfaces
            ),
        )

        print(
            "Ports extracted:",
            len(
                architecture.ports
            ),
        )

        print(
            "Signals extracted:",
            len(
                architecture.signals
            ),
        )

        print(
            "Dependencies extracted:",
            len(
                architecture.dependencies
            ),
        )

        print(
            "Component precision:",
            round(
                component_precision,
                3,
            ),
        )

        print(
            "Component recall:",
            round(
                component_recall,
                3,
            ),
        )

        print(
            "Interface precision:",
            round(
                interface_precision,
                3,
            ),
        )

        print(
            "Interface recall:",
            round(
                interface_recall,
                3,
            ),
        )

        if issues:

            print(
                "Detected structural issues:"
            )

            for issue in issues:

                print(
                    " -",
                    issue.issue_type,
                    ":",
                    issue.message,
                )

        else:

            print(
                "Detected structural issues: none"
            )

        print(
            "-" * 60
        )


if __name__ == "__main__":
    main()