from __future__ import annotations

from typing import Dict, List

from app.external_validation.arxml_parser import (
    ARXMLExtractionResult,
)

from app.models.architecture import (
    ArchitectureModel,
    Component,
    Interface,
    Port,
    Dependency,
)


class AUTOSARArchitectureAdapter:
    """
    Convert official AUTOSAR ARXML extraction results into the
    project's common ArchitectureModel.

    This allows the PDF/HLD pipeline and the public AUTOSAR
    validation pipeline to share the same downstream
    architecture representation.
    """

    def __init__(
        self,
        extraction: ARXMLExtractionResult,
    ):
        self.extraction = extraction

        # Build:
        #
        # CPT_VehSpdCalc -> VehSpdCalc
        # CPT_VehSpdActr -> VehSpdActr
        #
        # directly from TYPE-TREF information extracted
        # from the ARXML.

        self.instance_to_type: Dict[str, str] = {
            instance.instance_name: instance.component_type
            for instance in extraction.instances
        }

    # =====================================================
    # COMPONENT RESOLUTION
    # =====================================================

    def _resolve_component(
        self,
        component_name: str,
    ) -> str:
        """
        Resolve an AUTOSAR SW-COMPONENT-PROTOTYPE instance
        name to its actual component type.

        If no mapping exists, preserve the original name
        rather than guessing.
        """

        return self.instance_to_type.get(
            component_name,
            component_name,
        )

    # =====================================================
    # CONVERSION
    # =====================================================

    def to_architecture_model(
        self,
        filename: str = "AUTOSAR_WorkflowExample",
    ) -> ArchitectureModel:

        # -------------------------------------------------
        # COMPONENTS
        # -------------------------------------------------

        components: List[Component] = []

        component_names = set()

        for component in self.extraction.components:

            if component.name in component_names:
                continue

            components.append(
                Component(
                    name=component.name,
                    description=(
                        "Extracted from official AUTOSAR ARXML. "
                        f"Type: {component.component_type}"
                    ),
                )
            )

            component_names.add(component.name)

        # -------------------------------------------------
        # PORTS
        # -------------------------------------------------

        ports: List[Port] = []

        for port in self.extraction.ports:

            ports.append(
                Port(
                    component=port.component,
                    name=port.name,
                    port_type=port.port_type,
                    interface=port.interface,
                )
            )

        # -------------------------------------------------
        # ACTIVE INTERFACES
        # -------------------------------------------------
        #
        # The public AUTOSAR package contains a large
        # interface catalogue.
        #
        # We do NOT put all catalogue definitions into the
        # active ArchitectureModel.
        #
        # Only interfaces actually referenced by extracted
        # component ports are included here.
        # -------------------------------------------------

        active_interface_names = sorted(
            {
                port.interface
                for port in self.extraction.ports
                if port.interface
            }
        )

        interfaces: List[Interface] = []

        for interface_name in active_interface_names:

            providers = sorted(
                {
                    port.component
                    for port in self.extraction.ports
                    if (
                        port.interface == interface_name
                        and port.port_type
                        in {"P-Port", "PR-Port"}
                    )
                }
            )

            consumers = sorted(
                {
                    port.component
                    for port in self.extraction.ports
                    if (
                        port.interface == interface_name
                        and port.port_type
                        in {"R-Port", "PR-Port"}
                    )
                }
            )

            interfaces.append(
                Interface(
                    name=interface_name,
                    provider=", ".join(providers),
                    consumer=", ".join(consumers),
                )
            )

        # -------------------------------------------------
        # DEPENDENCIES
        # -------------------------------------------------
        #
        # AUTOSAR assembly connector:
        #
        # Provider ---> Requester
        #
        # therefore:
        #
        # Requester depends on Provider
        #
        # Example:
        #
        # CPT_VehSpdCalc -> CPT_VehSpdActr
        #
        # resolves to:
        #
        # VehSpdActr depends on VehSpdCalc
        # -------------------------------------------------

        dependencies: List[Dependency] = []

        dependency_keys = set()

        for connector in self.extraction.connectors:

            provider = self._resolve_component(
                connector.provider_component
            )

            requester = self._resolve_component(
                connector.requester_component
            )

            if not provider or not requester:
                continue

            dependency_key = (
                requester,
                provider,
            )

            if dependency_key in dependency_keys:
                continue

            dependency_keys.add(
                dependency_key
            )

            dependencies.append(
                Dependency(
                    dependent_component=requester,
                    required_component=provider,
                )
            )

            # Normally these component types already exist
            # in extraction.components.
            #
            # If an assembly connector references a valid
            # resolved type not present there, preserve it
            # so that we never create a dangling dependency.

            for name in (
                provider,
                requester,
            ):

                if name not in component_names:

                    components.append(
                        Component(
                            name=name,
                            description=(
                                "Resolved from AUTOSAR "
                                "SW-COMPONENT-PROTOTYPE."
                            ),
                        )
                    )

                    component_names.add(name)

        # -------------------------------------------------
        # FINAL COMMON ARCHITECTURE MODEL
        # -------------------------------------------------

        return ArchitectureModel(
            filename=filename,
            document_id=(
                "AUTOSAR-OFFICIAL-WORKFLOW-EXAMPLE"
            ),
            version="public-example",
            components=components,
            interfaces=interfaces,
            ports=ports,

            # We have not implemented AUTOSAR data-element /
            # signal extraction yet, so do not fabricate
            # signals.
            signals=[],

            dependencies=dependencies,
        )