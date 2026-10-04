from app.extraction.architecture_extractor import (
    ArchitectureExtractor,
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


def main():

    extractor = ArchitectureExtractor()
    checker = ConsistencyChecker()

    print(
        "\n================================="
    )
    print(
        "AUTOSAR ARCHITECTURE VALIDATION"
    )
    print(
        "================================="
    )

    for filename in DOCUMENTS:

        architecture = extractor.extract(
            filename
        )

        issues = checker.validate(
            architecture
        )

        print(
            f"\nDOCUMENT: {filename}"
        )

        print(
            f"Components: "
            f"{len(architecture.components)}"
        )

        print(
            f"Interfaces: "
            f"{len(architecture.interfaces)}"
        )

        print(
            f"Ports: "
            f"{len(architecture.ports)}"
        )

        print(
            f"Signals: "
            f"{len(architecture.signals)}"
        )

        if not issues:

            print(
                "Validation: "
                "No structural issues detected."
            )

        else:

            print(
                f"Validation issues: "
                f"{len(issues)}"
            )

            for issue in issues:

                print(
                    f"  [{issue.severity.upper()}] "
                    f"{issue.issue_type}: "
                    f"{issue.message}"
                )

        print(
            "-" * 60
        )


if __name__ == "__main__":
    main()