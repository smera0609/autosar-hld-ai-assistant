from pathlib import Path

from app.external_validation.arxml_parser import (
    AUTOSARARXMLParser,
)

from app.external_validation.architecture_adapter import (
    AUTOSARArchitectureAdapter,
)

from app.graph.architecture_graph import (
    ArchitectureGraph,
)


AUTOSAR_ROOT = Path(
    "data/public_autosar/AUTOSAR_WorkflowExample"
)


def main():

    print("=" * 70)
    print("OFFICIAL AUTOSAR -> COMMON MODEL -> GRAPH TEST")
    print("=" * 70)

    # =====================================================
    # 1. PARSE OFFICIAL AUTOSAR ARXML
    # =====================================================

    parser = AUTOSARARXMLParser(
        AUTOSAR_ROOT
    )

    extraction = parser.parse_directory()

    assert extraction.files_processed > 0
    assert not extraction.parse_errors

    print()
    print("ARXML parsed successfully.")
    print(
        "Files processed:",
        extraction.files_processed,
    )

    # =====================================================
    # 2. CONVERT TO COMMON ARCHITECTURE MODEL
    # =====================================================

    adapter = AUTOSARArchitectureAdapter(
        extraction
    )

    architecture = (
        adapter.to_architecture_model()
    )

    print()
    print("COMMON ARCHITECTURE MODEL")
    print("-" * 70)

    print(
        "Components:",
        len(architecture.components),
    )

    print(
        "Interfaces:",
        len(architecture.interfaces),
    )

    print(
        "Ports:",
        len(architecture.ports),
    )

    print(
        "Dependencies:",
        len(architecture.dependencies),
    )

    # =====================================================
    # 3. BUILD GRAPH USING EXISTING PROJECT GRAPH ENGINE
    # =====================================================

    graph_engine = ArchitectureGraph()

    graph = graph_engine.build(
        architecture
    )

    print()
    print("GRAPH")
    print("-" * 70)

    print(
        "Nodes:",
        graph.number_of_nodes(),
    )

    print(
        "Edges:",
        graph.number_of_edges(),
    )

    # =====================================================
    # 4. NODE TYPE SUMMARY
    # =====================================================

    node_types = {}

    for _, data in graph.nodes(data=True):

        node_type = data.get(
            "type",
            "unknown",
        )

        node_types[node_type] = (
            node_types.get(node_type, 0) + 1
        )

    print()
    print("NODE TYPES")
    print("-" * 70)

    for node_type, count in sorted(
        node_types.items()
    ):
        print(
            node_type,
            ":",
            count,
        )

    # =====================================================
    # 5. RELATIONSHIP SUMMARY
    # =====================================================

    relationships = {}

    for _, _, data in graph.edges(data=True):

        relationship = data.get(
            "relationship",
            "unknown",
        )

        relationships[relationship] = (
            relationships.get(
                relationship,
                0,
            )
            + 1
        )

    print()
    print("RELATIONSHIPS")
    print("-" * 70)

    for relationship, count in sorted(
        relationships.items()
    ):
        print(
            relationship,
            ":",
            count,
        )

    # =====================================================
    # 6. SHOW DEPENDENCY EDGES
    # =====================================================

    print()
    print("DEPENDENCY EDGES")
    print("-" * 70)

    dependency_edges = []

    for source, target, data in graph.edges(
        data=True
    ):

        if (
            data.get("relationship")
            == "DEPENDS_ON"
        ):

            dependency_edges.append(
                (source, target)
            )

            print(
                source,
                "--DEPENDS_ON-->",
                target,
            )

    # =====================================================
    # 7. VALIDATION
    # =====================================================

    print()
    print("VALIDATION")
    print("-" * 70)

    assert graph.number_of_nodes() > 0

    assert graph.number_of_edges() > 0

    assert dependency_edges, (
        "No dependency edges were created."
    )

    # Verify known official AUTOSAR relationship:
    #
    # VehSpdCalc provides information to VehSpdActr.
    #
    # Therefore:
    #
    # VehSpdActr DEPENDS_ON VehSpdCalc

    assert (
        "VehSpdActr",
        "VehSpdCalc",
    ) in dependency_edges, (
        "Expected VehSpdActr -> "
        "VehSpdCalc dependency missing."
    )

    # No unresolved CPT_ component instances
    # should remain as graph nodes.

    unresolved_nodes = [
        str(node)
        for node in graph.nodes()
        if str(node).startswith("CPT_")
    ]

    assert not unresolved_nodes, (
        "Unresolved component instances "
        f"found: {unresolved_nodes}"
    )

    print(
        "Graph contains architecture relationships."
    )

    print(
        "Known AUTOSAR dependency verified."
    )

    print(
        "No unresolved CPT_ instance nodes."
    )

    print()
    print("=" * 70)
    print(
        "OFFICIAL AUTOSAR GRAPH TEST PASSED"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()