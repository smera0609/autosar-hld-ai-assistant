from __future__ import annotations

import json
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

OUTPUT_FILE = Path(
    "outputs/external_autosar_validation.json"
)


def main():

    # -----------------------------------------------------
    # Parse official AUTOSAR artifacts
    # -----------------------------------------------------

    parser = AUTOSARARXMLParser(
        AUTOSAR_ROOT
    )

    extraction = parser.parse_directory()

    # -----------------------------------------------------
    # Convert to common architecture representation
    # -----------------------------------------------------

    adapter = AUTOSARArchitectureAdapter(
        extraction
    )

    architecture = (
        adapter.to_architecture_model()
    )

    # -----------------------------------------------------
    # Build graph using existing graph engine
    # -----------------------------------------------------

    graph_engine = ArchitectureGraph()

    graph = graph_engine.build(
        architecture
    )

    # -----------------------------------------------------
    # Relationship statistics
    # -----------------------------------------------------

    relationship_counts = {}

    for _, _, data in graph.edges(data=True):

        relationship = data.get(
            "relationship",
            "unknown",
        )

        relationship_counts[relationship] = (
            relationship_counts.get(
                relationship,
                0,
            )
            + 1
        )

    # -----------------------------------------------------
    # Component instance mappings
    # -----------------------------------------------------

    instance_mappings = [
        {
            "instance": instance.instance_name,
            "component_type": instance.component_type,
            "category": (
                instance.component_type_category
            ),
        }
        for instance in extraction.instances
    ]

    # -----------------------------------------------------
    # Active interfaces
    # -----------------------------------------------------

    active_interfaces = [
        {
            "name": interface.name,
            "provider": interface.provider,
            "consumer": interface.consumer,
        }
        for interface in architecture.interfaces
    ]

    # -----------------------------------------------------
    # Resolved dependencies
    # -----------------------------------------------------

    dependencies = [
        {
            "dependent_component": (
                dependency.dependent_component
            ),
            "required_component": (
                dependency.required_component
            ),
        }
        for dependency in architecture.dependencies
    ]

    # -----------------------------------------------------
    # Assembly connectors
    # -----------------------------------------------------

    connectors = [
        {
            "name": connector.name,
            "provider_instance": (
                connector.provider_component
            ),
            "provider_port": (
                connector.provider_port
            ),
            "requester_instance": (
                connector.requester_component
            ),
            "requester_port": (
                connector.requester_port
            ),
        }
        for connector in extraction.connectors
    ]

    # -----------------------------------------------------
    # Validation checks
    # -----------------------------------------------------

    unresolved_dependency_instances = []

    for dependency in architecture.dependencies:

        if (
            dependency.dependent_component.startswith(
                "CPT_"
            )
            or dependency.required_component.startswith(
                "CPT_"
            )
        ):
            unresolved_dependency_instances.append(
                {
                    "dependent": (
                        dependency.dependent_component
                    ),
                    "required": (
                        dependency.required_component
                    ),
                }
            )

    component_names = {
        component.name
        for component in architecture.components
    }

    dangling_dependencies = []

    for dependency in architecture.dependencies:

        if (
            dependency.dependent_component
            not in component_names
            or dependency.required_component
            not in component_names
        ):
            dangling_dependencies.append(
                {
                    "dependent": (
                        dependency.dependent_component
                    ),
                    "required": (
                        dependency.required_component
                    ),
                }
            )

    validation_passed = (
        extraction.files_processed > 0
        and len(extraction.parse_errors) == 0
        and len(extraction.components) > 0
        and len(extraction.ports) > 0
        and len(extraction.connectors) > 0
        and len(architecture.dependencies) > 0
        and len(unresolved_dependency_instances) == 0
        and len(dangling_dependencies) == 0
    )

    # -----------------------------------------------------
    # Final report
    # -----------------------------------------------------

    report = {
        "validation_name": (
            "Official AUTOSAR External Validation"
        ),

        "dataset": (
            "AUTOSAR Classic Platform "
            "Workflow Example"
        ),

        "data_classification": (
            "Public external AUTOSAR "
            "validation artifacts"
        ),

        "purpose": (
            "Evaluate compatibility and generalization "
            "of the architecture-analysis representation "
            "using official AUTOSAR artifacts. "
            "This is separate from the controlled "
            "synthetic HLD accuracy benchmark."
        ),

        "arxml_extraction": {
            "files_processed": (
                extraction.files_processed
            ),
            "parse_errors": len(
                extraction.parse_errors
            ),
            "component_definitions": len(
                extraction.components
            ),
            "port_definitions": len(
                extraction.ports
            ),
            "interface_catalogue_definitions": len(
                extraction.interfaces
            ),
            "component_instances": len(
                extraction.instances
            ),
            "assembly_connectors": len(
                extraction.connectors
            ),
        },

        "common_architecture_model": {
            "components": len(
                architecture.components
            ),
            "active_interfaces": len(
                architecture.interfaces
            ),
            "ports": len(
                architecture.ports
            ),
            "signals": len(
                architecture.signals
            ),
            "dependencies": len(
                architecture.dependencies
            ),
        },

        "graph": {
            "nodes": graph.number_of_nodes(),
            "edges": graph.number_of_edges(),
            "relationships": (
                relationship_counts
            ),
        },

        "component_instance_mappings": (
            instance_mappings
        ),

        "active_interfaces": (
            active_interfaces
        ),

        "assembly_connectors": (
            connectors
        ),

        "resolved_dependencies": (
            dependencies
        ),

        "validation": {
            "parse_success": (
                len(extraction.parse_errors) == 0
            ),
            "all_dependency_instances_resolved": (
                len(
                    unresolved_dependency_instances
                )
                == 0
            ),
            "no_dangling_dependencies": (
                len(dangling_dependencies) == 0
            ),
            "overall_passed": (
                validation_passed
            ),
        },

        "limitations": [
            (
                "This external dataset is an official "
                "AUTOSAR workflow example, not a "
                "production OEM HLD dataset."
            ),
            (
                "The external validation demonstrates "
                "format compatibility and architecture "
                "generalization; it does not represent "
                "ground-truth precision or recall."
            ),
            (
                "Only assembly connectors are currently "
                "mapped into component dependencies."
            ),
            (
                "AUTOSAR data-element/signal extraction "
                "is not included in this external "
                "validation adapter."
            ),
        ],
    }

    # -----------------------------------------------------
    # Save report
    # -----------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            report,
            file,
            indent=2,
        )

    print("=" * 70)
    print("EXTERNAL AUTOSAR VALIDATION REPORT")
    print("=" * 70)

    print(
        "Output:",
        OUTPUT_FILE,
    )

    print(
        "Files processed:",
        extraction.files_processed,
    )

    print(
        "Components:",
        len(architecture.components),
    )

    print(
        "Active interfaces:",
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

    print(
        "Graph nodes:",
        graph.number_of_nodes(),
    )

    print(
        "Graph edges:",
        graph.number_of_edges(),
    )

    print(
        "Overall validation:",
        (
            "PASSED"
            if validation_passed
            else "FAILED"
        ),
    )

    print("=" * 70)


if __name__ == "__main__":
    main()