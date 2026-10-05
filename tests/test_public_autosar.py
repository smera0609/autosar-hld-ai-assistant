from pathlib import Path

from app.external_validation.arxml_parser import (
    AUTOSARARXMLParser,
)


def main():

    dataset_path = Path(
        "data/public_autosar/AUTOSAR_WorkflowExample"
    )

    parser = AUTOSARARXMLParser(dataset_path)

    result = parser.parse_directory()

    print()
    print("=" * 70)
    print("OFFICIAL AUTOSAR EXTERNAL VALIDATION")
    print("=" * 70)

    print(f"Dataset: {dataset_path}")
    print(f"ARXML files processed: {result.files_processed}")
    print(f"Parse errors: {len(result.parse_errors)}")

    # ---------------------------------------------------------
    # COMPONENTS
    # ---------------------------------------------------------

    print()
    print("-" * 70)
    print("SOFTWARE COMPONENTS")
    print("-" * 70)

    for component in result.components:
        print(
            f"{component.name:<30} "
            f"{component.component_type}"
        )

    print()
    print(f"Unique components: {len(result.components)}")

    # ---------------------------------------------------------
    # PORTS
    # ---------------------------------------------------------

    print()
    print("-" * 70)
    print("PORTS")
    print("-" * 70)

    for port in result.ports:
        print(
            f"{port.component:<25} "
            f"{port.port_type:<8} "
            f"{port.name:<25} "
            f"Interface: {port.interface}"
        )

    print()
    print(f"Unique ports: {len(result.ports)}")

    # ---------------------------------------------------------
    # INTERFACES
    # ---------------------------------------------------------

    print()
    print("-" * 70)
    print("INTERFACES")
    print("-" * 70)

    for interface in result.interfaces:
        print(
            f"{interface.name:<30} "
            f"{interface.interface_type}"
        )

    print()
    print(f"Unique interfaces: {len(result.interfaces)}")

    # ---------------------------------------------------------
    # ASSEMBLY CONNECTORS
    # ---------------------------------------------------------

    print()
    print("-" * 70)
    print("ASSEMBLY CONNECTORS")
    print("-" * 70)

    for connector in result.connectors:

        print()
        print(f"Connector: {connector.name}")

        print(
            f"  Provider : "
            f"{connector.provider_component}"
            f" / {connector.provider_port}"
        )

        print(
            f"  Requester: "
            f"{connector.requester_component}"
            f" / {connector.requester_port}"
        )

    print()
    print(
        f"Unique assembly connectors: "
        f"{len(result.connectors)}"
    )

    # ---------------------------------------------------------
    # PARSE ERRORS
    # ---------------------------------------------------------

    if result.parse_errors:

        print()
        print("-" * 70)
        print("PARSE ERRORS")
        print("-" * 70)

        for error in result.parse_errors:
            print(error)

    # ---------------------------------------------------------
    # VALIDATION ASSERTIONS
    # ---------------------------------------------------------

    assert result.files_processed > 0, (
        "No official AUTOSAR ARXML files were processed."
    )

    assert len(result.components) > 0, (
        "No AUTOSAR software components were extracted."
    )

    assert len(result.ports) > 0, (
        "No AUTOSAR ports were extracted."
    )

    assert len(result.interfaces) > 0, (
        "No AUTOSAR interfaces were extracted."
    )

    assert len(result.connectors) > 0, (
        "No AUTOSAR assembly connectors were extracted."
    )

    assert len(result.parse_errors) == 0, (
        "One or more official AUTOSAR ARXML files "
        "could not be parsed."
    )

    # Every extracted assembly connector should contain
    # complete provider/requester information.
    for connector in result.connectors:

        assert connector.provider_component, (
            f"Missing provider component: {connector.name}"
        )

        assert connector.provider_port, (
            f"Missing provider port: {connector.name}"
        )

        assert connector.requester_component, (
            f"Missing requester component: {connector.name}"
        )

        assert connector.requester_port, (
            f"Missing requester port: {connector.name}"
        )

    print()
    print("=" * 70)
    print("EXTERNAL AUTOSAR VALIDATION PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()