from app.extraction.functional_flow_extractor import (
    FunctionalFlowExtractor,
)


FILES = [
    "Vehicle_Control_HLD_v1.pdf",
    "Vehicle_Control_HLD_v2.pdf",
    "Braking_System_HLD.pdf",
    "Door_Control_HLD.pdf",
    "Body_Control_HLD.pdf",
]


def main():

    extractor = FunctionalFlowExtractor()

    print()
    print("=" * 70)
    print("FUNCTIONAL FLOW EXTRACTION TEST")
    print("=" * 70)

    for filename in FILES:

        path = (
            "data/sample_hlds/"
            + filename
        )

        result = extractor.extract(path)

        print()
        print("-" * 70)
        print(filename)
        print("-" * 70)

        print(
            "Flow:",
            result["flow_text"]
        )

        print(
            "Nodes:",
            result["nodes"]
        )

        print("Edges:")

        for source, target in result["edges"]:
            print(
                f"  {source} -> {target}"
            )


if __name__ == "__main__":
    main()