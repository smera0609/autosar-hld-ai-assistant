from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List
import xml.etree.ElementTree as ET


# =========================================================
# DATA MODELS
# =========================================================

@dataclass
class ARXMLComponent:
    name: str
    component_type: str
    source_file: str


@dataclass
class ARXMLPort:
    component: str
    name: str
    port_type: str
    interface: str
    source_file: str


@dataclass
class ARXMLInterface:
    name: str
    interface_type: str
    source_file: str


@dataclass
class ARXMLComponentInstance:
    """
    AUTOSAR SW-COMPONENT-PROTOTYPE instance mapped
    to its underlying software-component type.

    Example:
        CPT_VehSpdCalc -> VehSpdCalc
    """

    instance_name: str
    component_type: str
    component_type_category: str
    source_file: str


@dataclass
class ARXMLConnector:
    """
    Represents an AUTOSAR assembly connector.

    provider_component and requester_component are component INSTANCE
    names obtained from CONTEXT-COMPONENT-REF.

    provider_port and requester_port are the corresponding P/R ports.
    """

    name: str
    provider_component: str
    provider_port: str
    requester_component: str
    requester_port: str
    connector_type: str
    source_file: str


@dataclass
class ARXMLExtractionResult:
    components: List[ARXMLComponent] = field(default_factory=list)
    ports: List[ARXMLPort] = field(default_factory=list)
    interfaces: List[ARXMLInterface] = field(default_factory=list)
    connectors: List[ARXMLConnector] = field(default_factory=list)
    instances: List[ARXMLComponentInstance] = field(default_factory=list)

    files_processed: int = 0
    parse_errors: List[str] = field(default_factory=list)


# =========================================================
# AUTOSAR ARXML PARSER
# =========================================================

class AUTOSARARXMLParser:
    """
    Lightweight external-validation parser for public AUTOSAR ARXML.

    This parser is intentionally separate from the project's PDF/HLD
    extraction pipeline.

    It is used to test whether the project's architecture concepts
    generalize to official AUTOSAR artifacts.
    """

    COMPONENT_TAGS = {
        "APPLICATION-SW-COMPONENT-TYPE",
        "COMPOSITION-SW-COMPONENT-TYPE",
        "SENSOR-ACTUATOR-SW-COMPONENT-TYPE",
        "ECU-ABSTRACTION-SW-COMPONENT-TYPE",
        "SERVICE-SW-COMPONENT-TYPE",
        "COMPLEX-DEVICE-DRIVER-SW-COMPONENT-TYPE",
    }

    INTERFACE_TAGS = {
        "SENDER-RECEIVER-INTERFACE",
        "CLIENT-SERVER-INTERFACE",
        "MODE-SWITCH-INTERFACE",
        "NV-DATA-INTERFACE",
        "TRIGGER-INTERFACE",
    }

    def __init__(self, root_directory: str | Path):
        self.root_directory = Path(root_directory)

    # =====================================================
    # XML HELPERS
    # =====================================================

    @staticmethod
    def _local_name(tag: str) -> str:
        """
        Remove XML namespace from a tag.
        """

        if "}" in tag:
            return tag.split("}", 1)[1]

        return tag

    def _direct_child_text(
        self,
        element: ET.Element,
        child_name: str,
    ) -> str:
        """
        Return text from a direct child with the requested
        local tag name.
        """

        for child in element:

            if self._local_name(child.tag) == child_name:
                return (child.text or "").strip()

        return ""

    def _first_descendant_text(
        self,
        element: ET.Element,
        descendant_name: str,
    ) -> str:
        """
        Return the text of the first descendant with
        the requested local tag name.
        """

        for descendant in element.iter():

            if self._local_name(descendant.tag) == descendant_name:
                return (descendant.text or "").strip()

        return ""

    def _first_descendant(
        self,
        element: ET.Element,
        descendant_name: str,
    ) -> ET.Element | None:
        """
        Return the first descendant element with the
        requested local tag.
        """

        for descendant in element.iter():

            if self._local_name(descendant.tag) == descendant_name:
                return descendant

        return None

    @staticmethod
    def _reference_short_name(reference: str) -> str:
        """
        Convert an AUTOSAR reference path to its final short name.

        Example:

        /AUTOSAR_AISpecification/PortInterfaces/VehSpd1

        becomes:

        VehSpd1
        """

        if not reference:
            return ""

        return reference.rstrip("/").split("/")[-1]

    # =====================================================
    # COMPONENT EXTRACTION
    # =====================================================

    def _extract_component(
        self,
        element: ET.Element,
        source_file: Path,
    ) -> ARXMLComponent | None:

        tag_name = self._local_name(element.tag)

        if tag_name not in self.COMPONENT_TAGS:
            return None

        name = self._direct_child_text(
            element,
            "SHORT-NAME",
        )

        if not name:
            return None

        return ARXMLComponent(
            name=name,
            component_type=tag_name,
            source_file=str(source_file),
        )

    # =====================================================
    # PORT EXTRACTION
    # =====================================================

    def _extract_ports(
        self,
        component_element: ET.Element,
        component_name: str,
        source_file: Path,
    ) -> List[ARXMLPort]:

        ports: List[ARXMLPort] = []

        for element in component_element.iter():

            tag_name = self._local_name(element.tag)

            if tag_name not in {
                "P-PORT-PROTOTYPE",
                "R-PORT-PROTOTYPE",
                "PR-PORT-PROTOTYPE",
            }:
                continue

            port_name = self._direct_child_text(
                element,
                "SHORT-NAME",
            )

            interface_reference = ""

            if tag_name == "P-PORT-PROTOTYPE":

                interface_reference = self._direct_child_text(
                    element,
                    "PROVIDED-INTERFACE-TREF",
                )

                port_type = "P-Port"

            elif tag_name == "R-PORT-PROTOTYPE":

                interface_reference = self._direct_child_text(
                    element,
                    "REQUIRED-INTERFACE-TREF",
                )

                port_type = "R-Port"

            else:

                interface_reference = self._direct_child_text(
                    element,
                    "PROVIDED-REQUIRED-INTERFACE-TREF",
                )

                port_type = "PR-Port"

            if not port_name:
                continue

            ports.append(
                ARXMLPort(
                    component=component_name,
                    name=port_name,
                    port_type=port_type,
                    interface=self._reference_short_name(
                        interface_reference
                    ),
                    source_file=str(source_file),
                )
            )

        return ports

    # =====================================================
    # INTERFACE EXTRACTION
    # =====================================================

    def _extract_interfaces(
        self,
        root: ET.Element,
        source_file: Path,
    ) -> List[ARXMLInterface]:

        interfaces: List[ARXMLInterface] = []

        for element in root.iter():

            tag_name = self._local_name(element.tag)

            if tag_name not in self.INTERFACE_TAGS:
                continue

            name = self._direct_child_text(
                element,
                "SHORT-NAME",
            )

            if not name:
                continue

            interfaces.append(
                ARXMLInterface(
                    name=name,
                    interface_type=tag_name,
                    source_file=str(source_file),
                )
            )

        return interfaces

    # =====================================================
    # COMPONENT INSTANCE EXTRACTION
    # =====================================================

    def _extract_component_instances(
        self,
        root: ET.Element,
        source_file: Path,
    ) -> List[ARXMLComponentInstance]:
        """
        Extract SW-COMPONENT-PROTOTYPE instance -> component type
        mappings.

        Example:

            CPT_VehSpdCalc
                    ->
            VehSpdCalc

        TYPE-TREF is used instead of guessing the type name
        from the instance name.
        """

        instances: List[ARXMLComponentInstance] = []

        for element in root.iter():

            tag_name = self._local_name(element.tag)

            if tag_name != "SW-COMPONENT-PROTOTYPE":
                continue

            instance_name = self._direct_child_text(
                element,
                "SHORT-NAME",
            )

            type_reference = self._direct_child_text(
                element,
                "TYPE-TREF",
            )

            if not instance_name or not type_reference:
                continue

            component_type = self._reference_short_name(
                type_reference
            )

            component_type_category = ""

            # TYPE-TREF contains a DEST attribute which identifies
            # the AUTOSAR component category.
            #
            # Examples:
            #
            # APPLICATION-SW-COMPONENT-TYPE
            # SENSOR-ACTUATOR-SW-COMPONENT-TYPE
            # ECU-ABSTRACTION-SW-COMPONENT-TYPE
            # COMPOSITION-SW-COMPONENT-TYPE

            for child in element:

                if self._local_name(child.tag) == "TYPE-TREF":

                    component_type_category = (
                        child.attrib.get("DEST", "")
                    )

                    break

            instances.append(
                ARXMLComponentInstance(
                    instance_name=instance_name,
                    component_type=component_type,
                    component_type_category=component_type_category,
                    source_file=str(source_file),
                )
            )

        return instances

    # =====================================================
    # ASSEMBLY CONNECTOR EXTRACTION
    # =====================================================

    def _extract_connectors(
        self,
        root: ET.Element,
        source_file: Path,
    ) -> List[ARXMLConnector]:
        """
        Extract AUTOSAR ASSEMBLY-SW-CONNECTOR relationships.

        An assembly connector links:

        provider component instance + P-Port

                        ->

        requester component instance + R-Port
        """

        connectors: List[ARXMLConnector] = []

        for element in root.iter():

            tag_name = self._local_name(element.tag)

            if tag_name != "ASSEMBLY-SW-CONNECTOR":
                continue

            connector_name = self._direct_child_text(
                element,
                "SHORT-NAME",
            )

            provider_iref = self._first_descendant(
                element,
                "PROVIDER-IREF",
            )

            requester_iref = self._first_descendant(
                element,
                "REQUESTER-IREF",
            )

            if provider_iref is None or requester_iref is None:
                continue

            provider_component_reference = (
                self._first_descendant_text(
                    provider_iref,
                    "CONTEXT-COMPONENT-REF",
                )
            )

            provider_port_reference = (
                self._first_descendant_text(
                    provider_iref,
                    "TARGET-P-PORT-REF",
                )
            )

            requester_component_reference = (
                self._first_descendant_text(
                    requester_iref,
                    "CONTEXT-COMPONENT-REF",
                )
            )

            requester_port_reference = (
                self._first_descendant_text(
                    requester_iref,
                    "TARGET-R-PORT-REF",
                )
            )

            provider_component = self._reference_short_name(
                provider_component_reference
            )

            provider_port = self._reference_short_name(
                provider_port_reference
            )

            requester_component = self._reference_short_name(
                requester_component_reference
            )

            requester_port = self._reference_short_name(
                requester_port_reference
            )

            # Only store complete component-to-component
            # assembly relationships.

            if not all(
                [
                    connector_name,
                    provider_component,
                    provider_port,
                    requester_component,
                    requester_port,
                ]
            ):
                continue

            connectors.append(
                ARXMLConnector(
                    name=connector_name,
                    provider_component=provider_component,
                    provider_port=provider_port,
                    requester_component=requester_component,
                    requester_port=requester_port,
                    connector_type="ASSEMBLY-SW-CONNECTOR",
                    source_file=str(source_file),
                )
            )

        return connectors

    # =====================================================
    # SINGLE FILE PARSING
    # =====================================================

    def parse_file(
        self,
        file_path: str | Path,
    ) -> ARXMLExtractionResult:

        file_path = Path(file_path)

        result = ARXMLExtractionResult()

        try:

            tree = ET.parse(file_path)
            root = tree.getroot()

        except (ET.ParseError, OSError) as exc:

            result.parse_errors.append(
                f"{file_path}: {exc}"
            )

            return result

        result.files_processed = 1

        # -------------------------------------------------
        # Components and their ports
        # -------------------------------------------------

        for element in root.iter():

            component = self._extract_component(
                element,
                file_path,
            )

            if component is None:
                continue

            result.components.append(component)

            result.ports.extend(
                self._extract_ports(
                    component_element=element,
                    component_name=component.name,
                    source_file=file_path,
                )
            )

        # -------------------------------------------------
        # Interface definitions
        # -------------------------------------------------

        result.interfaces.extend(
            self._extract_interfaces(
                root,
                file_path,
            )
        )

        # -------------------------------------------------
        # Component prototype instance -> type mappings
        # -------------------------------------------------

        result.instances.extend(
            self._extract_component_instances(
                root,
                file_path,
            )
        )

        # -------------------------------------------------
        # Assembly connector relationships
        # -------------------------------------------------

        result.connectors.extend(
            self._extract_connectors(
                root,
                file_path,
            )
        )

        return result

    # =====================================================
    # DIRECTORY PARSING
    # =====================================================

    def parse_directory(self) -> ARXMLExtractionResult:

        final_result = ARXMLExtractionResult()

        if not self.root_directory.exists():

            raise FileNotFoundError(
                f"AUTOSAR directory does not exist: "
                f"{self.root_directory}"
            )

        arxml_files = sorted(
            self.root_directory.rglob("*.arxml")
        )

        # Ignore macOS metadata/resource-fork files.

        arxml_files = [
            path
            for path in arxml_files
            if "__MACOSX" not in path.parts
            and not path.name.startswith("._")
        ]

        for file_path in arxml_files:

            result = self.parse_file(file_path)

            final_result.files_processed += (
                result.files_processed
            )

            final_result.components.extend(
                result.components
            )

            final_result.ports.extend(
                result.ports
            )

            final_result.interfaces.extend(
                result.interfaces
            )

            final_result.connectors.extend(
                result.connectors
            )

            final_result.instances.extend(
                result.instances
            )

            final_result.parse_errors.extend(
                result.parse_errors
            )

        # -------------------------------------------------
        # Remove duplicates while preserving provenance.
        # -------------------------------------------------

        final_result.components = (
            self._deduplicate_components(
                final_result.components
            )
        )

        final_result.ports = (
            self._deduplicate_ports(
                final_result.ports
            )
        )

        final_result.interfaces = (
            self._deduplicate_interfaces(
                final_result.interfaces
            )
        )

        final_result.connectors = (
            self._deduplicate_connectors(
                final_result.connectors
            )
        )

        final_result.instances = (
            self._deduplicate_instances(
                final_result.instances
            )
        )

        return final_result

    # =====================================================
    # DEDUPLICATION
    # =====================================================

    @staticmethod
    def _deduplicate_components(
        components: List[ARXMLComponent],
    ) -> List[ARXMLComponent]:

        seen = set()
        output = []

        for component in components:

            key = (
                component.name,
                component.component_type,
            )

            if key in seen:
                continue

            seen.add(key)
            output.append(component)

        return output

    @staticmethod
    def _deduplicate_ports(
        ports: List[ARXMLPort],
    ) -> List[ARXMLPort]:

        seen = set()
        output = []

        for port in ports:

            key = (
                port.component,
                port.name,
                port.port_type,
                port.interface,
            )

            if key in seen:
                continue

            seen.add(key)
            output.append(port)

        return output

    @staticmethod
    def _deduplicate_interfaces(
        interfaces: List[ARXMLInterface],
    ) -> List[ARXMLInterface]:

        seen = set()
        output = []

        for interface in interfaces:

            key = (
                interface.name,
                interface.interface_type,
            )

            if key in seen:
                continue

            seen.add(key)
            output.append(interface)

        return output

    @staticmethod
    def _deduplicate_connectors(
        connectors: List[ARXMLConnector],
    ) -> List[ARXMLConnector]:

        seen = set()
        output = []

        for connector in connectors:

            key = (
                connector.name,
                connector.provider_component,
                connector.provider_port,
                connector.requester_component,
                connector.requester_port,
            )

            if key in seen:
                continue

            seen.add(key)
            output.append(connector)

        return output

    @staticmethod
    def _deduplicate_instances(
        instances: List[ARXMLComponentInstance],
    ) -> List[ARXMLComponentInstance]:

        seen = set()
        output = []

        for instance in instances:

            key = (
                instance.instance_name,
                instance.component_type,
                instance.component_type_category,
            )

            if key in seen:
                continue

            seen.add(key)
            output.append(instance)

        return output