from app.extraction.pdf_architecture_extractor import (
    PDFArchitectureExtractor,
)

from app.extraction.functional_flow_extractor import (
    FunctionalFlowExtractor,
)

from app.graph.architecture_graph import (
    ArchitectureGraph,
)


def main():

    file_path = (
        "data/sample_hlds/"
        "Vehicle_Control_HLD_v1.pdf"
    )

    # ---------------------------------------------------------
    # Extract architecture
    # ---------------------------------------------------------

    architecture_extractor = (
        PDFArchitectureExtractor()
    )

    architecture = (
        architecture_extractor.extract(
            file_path
        )
    )

    # ---------------------------------------------------------
    # Extract functional flow
    # ---------------------------------------------------------

    flow_extractor = (
        FunctionalFlowExtractor()
    )

    functional_flow = (
        flow_extractor.extract(
            file_path
        )
    )

    # ---------------------------------------------------------
    # Build graph
    # ---------------------------------------------------------

    graph_builder = (
        ArchitectureGraph()
    )

    graph = graph_builder.build(
        architecture,
        functional_flow,
    )

    summary = graph_builder.summary(
        graph
    )

    # ---------------------------------------------------------
    # Display summary
    # ---------------------------------------------------------

    print()
    print("=" * 70)
    print("ARCHITECTURE GRAPH TEST")
    print("=" * 70)

    print(
        "Nodes:",
        summary["nodes"]
    )

    print(
        "Edges:",
        summary["edges"]
    )

    print(
        "Node types:",
        summary["node_types"]
    )

    print(
        "Relationships:",
        summary["relationships"]
    )

    # ---------------------------------------------------------
    # Functional flow
    # ---------------------------------------------------------

    print()
    print("Functional Flow:")

    for source, target in functional_flow[
        "edges"
    ]:

        print(
            f"  {source} -> {target}"
        )

    # ---------------------------------------------------------
    # Component traceability
    # ---------------------------------------------------------

    component = (
        "VehicleSpeedController"
    )

    neighbors = (
        graph_builder.component_neighbors(
            graph,
            component,
        )
    )

    print()
    print(
        f"Traceability for {component}:"
    )

    print("Incoming:")

    for item in neighbors["incoming"]:

        print(
            f"  {item['entity']} "
            f"--{item['relationship']}--> "
            f"{component}"
        )

    print("Outgoing:")

    for item in neighbors["outgoing"]:

        print(
            f"  {component} "
            f"--{item['relationship']}--> "
            f"{item['entity']}"
        )

    # ---------------------------------------------------------
    # Assertions
    # ---------------------------------------------------------

    assert (
        summary["relationships"]
        .get("PROVIDES", 0)
        == 2
    )

    assert (
        summary["relationships"]
        .get("CONSUMED_BY", 0)
        == 2
    )

    assert (
        summary["relationships"]
        .get("CARRIES", 0)
        == 2
    )

    assert (
        summary["relationships"]
        .get("DEPENDS_ON", 0)
        == 2
    )

    assert (
        summary["relationships"]
        .get("FLOWS_TO", 0)
        == 2
    )

    assert (
        graph.number_of_nodes()
        == 7
    )

    assert (
        graph.number_of_edges()
        == 10
    )

    print()
    print(
        "GRAPH TEST PASSED"
    )


if __name__ == "__main__":
    main()