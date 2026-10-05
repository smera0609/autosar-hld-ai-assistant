from pathlib import Path

from app.external_validation.arxml_parser import (
    AUTOSARARXMLParser,
)

from app.external_validation.architecture_adapter import (
    AUTOSARArchitectureAdapter,
)


AUTOSAR_ROOT = Path(
    "data/public_autosar/AUTOSAR_WorkflowExample"
)


def main():

    print("=" * 70)
    print("OFFICIAL AUTOSAR -> COMMON ARCHITECTURE MODEL TEST")
    print("=" * 70)

    # -----------------------------------------------------
    # 1. Parse official AUTOSAR ARXML
    # -----------------------------------------------------

    parser = AUTOSARARXMLParser(
        AUTOSAR_ROOT
    )

    extraction = parser.parse_directory()

    print()
    print("ARXML EXTRACTION")
    print("-" * 70)

    print(
        "Files processed:",
        extraction.files_processed,
    )

    print(
        "Parse errors:",
        len(extraction.parse_errors),
    )

    print(
        "Component definitions:",
        len(extraction.components),
    )

    print(
        "Ports:",
        len(extraction.ports),
    )

    print(
        "Interface definitions:",
        len(extraction.interfaces),
    )

    print(
        "Component instances:",
        len(extraction.instances),
    )

    print(
        "Assembly connectors:",
        len(extraction.connectors),
    )

    # -----------------------------------------------------
    # 2. Convert to common ArchitectureModel
    # -----------------------------------------------------

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
        "Active interfaces:",
        len(architecture.interfaces),
    )

    print(
        "Ports:",
        len(architecture.ports),
    )

    print(
        "Signals:",
        len(architecture.signals),
    )

    print(
        "Dependencies:",
        len(architecture.dependencies),
    )

    # -----------------------------------------------------
    # 3. Show active interfaces
    # -----------------------------------------------------

    print()
    print("ACTIVE INTERFACES")
    print("-" * 70)

    for interface in architecture.interfaces:

        print()
        print(
            "Interface:",
            interface.name,
        )

        print(
            "  Provider:",
            interface.provider,
        )

        print(
            "  Consumer:",
            interface.consumer,
        )

    # -----------------------------------------------------
    # 4. Show resolved dependencies
    # -----------------------------------------------------

    print()
    print("RESOLVED DEPENDENCIES")
    print("-" * 70)

    for dependency in architecture.dependencies:

        print(
            dependency.dependent_component,
            "depends on",
            dependency.required_component,
        )

    # -----------------------------------------------------
    # 5. Validation checks
    # -----------------------------------------------------

    print()
    print("VALIDATION")
    print("-" * 70)

    assert extraction.files_processed > 0
    assert not extraction.parse_errors

    assert extraction.components
    assert extraction.ports
    assert extraction.interfaces
    assert extraction.instances
    assert extraction.connectors

    # We verified seven SW-COMPONENT-PROTOTYPE
    # mappings in this official example.
    assert len(extraction.instances) == 7

    component_names = {
        component.name
        for component in architecture.components
    }

    # Every port must reference a component
    # represented in the common model.
    for port in architecture.ports:

        assert port.component in component_names, (
            f"Port {port.name} references missing "
            f"component {port.component}"
        )

    # Every dependency endpoint must exist.
    for dependency in architecture.dependencies:

        assert (
            dependency.dependent_component
            in component_names
        ), (
            "Missing dependent component: "
            f"{dependency.dependent_component}"
        )

        assert (
            dependency.required_component
            in component_names
        ), (
            "Missing required component: "
            f"{dependency.required_component}"
        )

    # Important:
    # Connector instance names such as CPT_VehSpdCalc
    # must have been resolved to actual component types.

    for dependency in architecture.dependencies:

        assert not (
            dependency.dependent_component.startswith(
                "CPT_"
            )
        )

        assert not (
            dependency.required_component.startswith(
                "CPT_"
            )
        )

    # Verify a relationship we observed directly
    # in the official ARXML:
    #
    # VehSpdCalc provides VehSpdOutp to VehSpdActr.
    #
    # Therefore VehSpdActr depends on VehSpdCalc.

    dependency_pairs = {
        (
            dependency.dependent_component,
            dependency.required_component,
        )
        for dependency
        in architecture.dependencies
    }

    assert (
        "VehSpdActr",
        "VehSpdCalc",
    ) in dependency_pairs

    print(
        "All dependency endpoints exist."
    )

    print(
        "Component prototype instances were "
        "resolved to component types."
    )

    print(
        "Known VehSpdActr -> VehSpdCalc "
        "dependency verified."
    )

    print()
    print("=" * 70)
    print(
        "COMMON ARCHITECTURE MODEL TEST PASSED"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()