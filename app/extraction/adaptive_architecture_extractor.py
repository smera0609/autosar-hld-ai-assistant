import re
from pathlib import Path

import pdfplumber

from app.models.architecture import (
    ArchitectureModel,
    Component,
    Interface,
    Port,
    Signal,
    Dependency,
)


class AdaptiveArchitectureExtractor:
    """
    Layout-tolerant architecture extractor for AUTOSAR-style HLD PDFs.

    Strategy:
    1. Extract PDF tables.
    2. Normalize alternative table-header names.
    3. Extract components, interfaces, ports, signals and dependencies.
    4. Support port tables with or without an explicit Component column.
    5. Use structured prose as a fallback.
    6. Deduplicate the final architecture model.

    Ground-truth data is NOT used by this extractor.
    """

    HEADER_ALIASES = {
        # Components
        "component": "component",
        "component name": "component",
        "software component": "component",
        "software component name": "component",
        "sw component": "component",
        "swc": "component",

        "responsibility": "description",
        "description": "description",
        "function": "description",
        "purpose": "description",
        "role": "description",

        # Interfaces
        "interface": "interface",
        "interface name": "interface",
        "interface id": "interface",

        "provider": "provider",
        "provided by": "provider",
        "providing component": "provider",
        "provider component": "provider",

        "consumer": "consumer",
        "consumed by": "consumer",
        "requiring component": "consumer",
        "consumer component": "consumer",

        # Ports
        "port": "port",
        "port name": "port",

        "type": "port_type",
        "port type": "port_type",
        "direction": "port_type",

        # Signals
        "signal": "signal",
        "signal name": "signal",
        "data element": "signal",
        "data element name": "signal",

        "unit": "unit",
        "units": "unit",

        # Dependencies
        "dependent component": "dependent",
        "dependent": "dependent",
        "source component": "dependent",
        "from component": "dependent",

        "required component": "required",
        "required": "required",
        "target component": "required",
        "to component": "required",

        # Metadata
        "field": "field",
        "value": "value",
        "document id": "document_id",
        "document identifier": "document_id",
        "version": "version",
        "document version": "version",
    }

    PORT_TYPE_ALIASES = {
        "p-port": "P-Port",
        "p port": "P-Port",
        "pport": "P-Port",
        "provided port": "P-Port",
        "provider port": "P-Port",
        "provided": "P-Port",

        "r-port": "R-Port",
        "r port": "R-Port",
        "rport": "R-Port",
        "required port": "R-Port",
        "receiver port": "R-Port",
        "required": "R-Port",
    }

    def extract(self, file_path: str) -> ArchitectureModel:

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"PDF not found: {path}"
            )

        if path.suffix.lower() != ".pdf":
            raise ValueError(
                "Architecture extractor requires a PDF."
            )

        components = []
        interfaces = []
        ports = []
        signals = []
        dependencies = []

        document_id = ""
        version = ""

        full_text_parts = []

        with pdfplumber.open(path) as pdf:

            for page in pdf.pages:

                # --------------------------------
                # EXTRACT PAGE TEXT
                # --------------------------------

                page_text = page.extract_text() or ""

                if page_text:
                    full_text_parts.append(page_text)

                # --------------------------------
                # EXTRACT TABLES
                # --------------------------------

                tables = page.extract_tables() or []

                for table in tables:

                    cleaned = self._clean_table(table)

                    if len(cleaned) < 2:
                        continue

                    headers = [
                        self._canonical_header(cell)
                        for cell in cleaned[0]
                    ]

                    # ========================================
                    # DOCUMENT CONTROL TABLE
                    # ========================================

                    if (
                        "field" in headers
                        and "value" in headers
                    ):

                        field_index = headers.index(
                            "field"
                        )

                        value_index = headers.index(
                            "value"
                        )

                        for row in cleaned[1:]:

                            field = self._cell(
                                row,
                                field_index,
                            )

                            value = self._cell(
                                row,
                                value_index,
                            )

                            normalized_field = (
                                self._normalise(field)
                            )

                            if normalized_field in {
                                "document id",
                                "document identifier",
                            }:
                                document_id = value

                            elif normalized_field in {
                                "version",
                                "document version",
                            }:
                                version = value

                    # ========================================
                    # PORT TABLE
                    #
                    # Supports:
                    #
                    # Component | Port | Port Type | Interface
                    #
                    # AND:
                    #
                    # Port Name | Type | Interface | Description
                    #
                    # ========================================

                    elif (
                        "port" in headers
                        and "port_type" in headers
                        and "interface" in headers
                    ):

                        port_i = headers.index(
                            "port"
                        )

                        type_i = headers.index(
                            "port_type"
                        )

                        interface_i = headers.index(
                            "interface"
                        )

                        component_i = (
                            headers.index("component")
                            if "component" in headers
                            else None
                        )

                        for row in cleaned[1:]:

                            port_name = self._cell(
                                row,
                                port_i,
                            )

                            if not port_name:
                                continue

                            # If the table has an explicit
                            # Component column, use it.
                            if component_i is not None:

                                component_name = self._cell(
                                    row,
                                    component_i,
                                )

                            else:

                                # Long HLD format may encode
                                # component ownership in port name:
                                #
                                # BodyControlManagerOut
                                # BodyControlManagerIn
                                #
                                # Remove terminal In/Out.
                                component_name = re.sub(
                                    r"(?:In|Out)$",
                                    "",
                                    port_name,
                                ).strip()

                            ports.append(
                                Port(
                                    component=component_name,
                                    name=port_name,
                                    port_type=self._port_type(
                                        self._cell(
                                            row,
                                            type_i,
                                        )
                                    ),
                                    interface=self._cell(
                                        row,
                                        interface_i,
                                    ),
                                )
                            )

                    # ========================================
                    # INTERFACE TABLE
                    # ========================================

                    elif (
                        "interface" in headers
                        and "provider" in headers
                        and "consumer" in headers
                    ):

                        interface_i = headers.index(
                            "interface"
                        )

                        provider_i = headers.index(
                            "provider"
                        )

                        consumer_i = headers.index(
                            "consumer"
                        )

                        for row in cleaned[1:]:

                            name = self._cell(
                                row,
                                interface_i,
                            )

                            if not name:
                                continue

                            interfaces.append(
                                Interface(
                                    name=name,
                                    provider=self._cell(
                                        row,
                                        provider_i,
                                    ),
                                    consumer=self._cell(
                                        row,
                                        consumer_i,
                                    ),
                                )
                            )

                    # ========================================
                    # SIGNAL TABLE
                    # ========================================

                    elif (
                        "signal" in headers
                        and "interface" in headers
                    ):

                        signal_i = headers.index(
                            "signal"
                        )

                        interface_i = headers.index(
                            "interface"
                        )

                        unit_i = (
                            headers.index("unit")
                            if "unit" in headers
                            else None
                        )

                        for row in cleaned[1:]:

                            name = self._cell(
                                row,
                                signal_i,
                            )

                            if not name:
                                continue

                            signals.append(
                                Signal(
                                    name=name,
                                    interface=self._cell(
                                        row,
                                        interface_i,
                                    ),
                                    unit=(
                                        self._cell(
                                            row,
                                            unit_i,
                                        )
                                        if unit_i is not None
                                        else ""
                                    ),
                                )
                            )

                    # ========================================
                    # DEPENDENCY TABLE
                    # ========================================

                    elif (
                        "dependent" in headers
                        and "required" in headers
                    ):

                        dependent_i = headers.index(
                            "dependent"
                        )

                        required_i = headers.index(
                            "required"
                        )

                        for row in cleaned[1:]:

                            dependent = self._cell(
                                row,
                                dependent_i,
                            )

                            required = self._cell(
                                row,
                                required_i,
                            )

                            if dependent and required:

                                dependencies.append(
                                    Dependency(
                                        dependent_component=dependent,
                                        required_component=required,
                                    )
                                )

                    # ========================================
                    # COMPONENT TABLE
                    # ========================================

                    elif (
                        "component" in headers
                        and "description" in headers
                    ):

                        component_i = headers.index(
                            "component"
                        )

                        description_i = headers.index(
                            "description"
                        )

                        for row in cleaned[1:]:

                            name = self._cell(
                                row,
                                component_i,
                            )

                            if not name:
                                continue

                            components.append(
                                Component(
                                    name=name,
                                    description=self._cell(
                                        row,
                                        description_i,
                                    ),
                                )
                            )

        # ============================================
        # COMBINE EXTRACTED PAGE TEXT
        # ============================================

        full_text = "\n".join(
            full_text_parts
        )

        # ============================================
        # METADATA FALLBACK
        # ============================================

        if not document_id:

            match = re.search(
                r"\bDocument\s*(?:ID|Identifier)"
                r"\s*[:\-]\s*"
                r"([A-Za-z0-9_.\-]+)",
                full_text,
                flags=re.IGNORECASE,
            )

            if match:
                document_id = (
                    match.group(1).strip()
                )

        if not version:

            match = re.search(
                r"\bVersion\s*[:\-]\s*"
                r"([A-Za-z0-9_.\-]+)",
                full_text,
                flags=re.IGNORECASE,
            )

            if match:
                version = (
                    match.group(1).strip()
                )

        # ============================================
        # COMPONENT PROSE FALLBACK
        #
        # Example:
        #
        # 4. Component Design - BodyControlManager
        # Responsibility. Coordinates body-control...
        # ============================================

        component_pattern = re.compile(
            r"(?:^|\n)"
            r"\s*\d+(?:\.\d+)*\.?\s*"
            r"Component\s+Design\s*[-:]\s*"
            r"([A-Za-z][A-Za-z0-9_]*)"
            r"\s*\n"
            r"(?:Responsibility\s*[.:]\s*)"
            r"([^\n]+)",
            flags=re.IGNORECASE,
        )

        for match in component_pattern.finditer(
            full_text
        ):

            components.append(
                Component(
                    name=match.group(1).strip(),
                    description=(
                        match.group(2).strip()
                    ),
                )
            )

        # ============================================
        # INTERFACE PROSE FALLBACK
        #
        # Example:
        #
        # "The principal interface ... is
        #  LightRequestInterface"
        # ============================================

        interface_pattern = re.compile(
            r"(?:principal|primary)\s+interface"
            r"(?:\s+for\s+this\s+component)?"
            r"\s*(?:is|[:\-])\s*"
            r"([A-Za-z][A-Za-z0-9_]*)",
            flags=re.IGNORECASE,
        )

        discovered_interfaces = {
            item.name.lower()
            for item in interfaces
            if item.name
        }

        for match in interface_pattern.finditer(
            full_text
        ):

            name = match.group(1).strip()

            if (
                name.lower()
                not in discovered_interfaces
            ):

                interfaces.append(
                    Interface(
                        name=name,
                        provider="",
                        consumer="",
                    )
                )

                discovered_interfaces.add(
                    name.lower()
                )

        # ============================================
        # DEPENDENCY PROSE FALLBACK
        #
        # Looks inside each component section.
        #
        # Example:
        #
        # Requires LightSwitch and DoorStateManager.
        # ============================================

        section_pattern = re.compile(
            r"Component\s+Design\s*[-:]\s*"
            r"([A-Za-z][A-Za-z0-9_]*)"
            r"(.*?)"
            r"(?="
            r"\n\s*\d+(?:\.\d+)*\.?\s*"
            r"Component\s+Design\s*[-:]"
            r"|\Z)",
            flags=(
                re.IGNORECASE
                | re.DOTALL
            ),
        )

        for section_match in (
            section_pattern.finditer(
                full_text
            )
        ):

            component_name = (
                section_match
                .group(1)
                .strip()
            )

            section_text = (
                section_match.group(2)
            )

            dep_match = re.search(
                r"(?:Dependency[^:\n]*"
                r"[:.]?\s*)?"
                r"Requires\s+"
                r"([A-Za-z0-9_,\s\-]+?)"
                r"(?:\.|\n)",
                section_text,
                flags=re.IGNORECASE,
            )

            if not dep_match:
                continue

            required_text = (
                dep_match.group(1)
            )

            required_text = re.sub(
                r"\band\b",
                ",",
                required_text,
                flags=re.IGNORECASE,
            )

            for required in (
                required_text.split(",")
            ):

                required = required.strip()

                if (
                    required
                    and required.lower()
                    not in {
                        "none",
                        "no upstream software component",
                    }
                ):

                    dependencies.append(
                        Dependency(
                            dependent_component=(
                                component_name
                            ),
                            required_component=(
                                required
                            ),
                        )
                    )

        # ============================================
        # INFER INTERFACE PROVIDERS / CONSUMERS
        # FROM PORT EVIDENCE
        #
        # P-Port -> provider
        # R-Port -> consumer
        # ============================================

        interface_map = {}

        # First preserve interfaces already found.
        for interface in interfaces:

            if not interface.name:
                continue

            key = interface.name.lower()

            interface_map[key] = {
                "name": interface.name,
                "provider": (
                    interface.provider or ""
                ),
                "consumer": (
                    interface.consumer or ""
                ),
            }

        # Then enrich/create interfaces using ports.
        for port in ports:

            interface_name = (
                port.interface.strip()
                if port.interface
                else ""
            )

            component_name = (
                port.component.strip()
                if port.component
                else ""
            )

            if (
                not interface_name
                or not component_name
            ):
                continue

            key = interface_name.lower()

            if key not in interface_map:

                interface_map[key] = {
                    "name": interface_name,
                    "provider": "",
                    "consumer": "",
                }

            normalized_port_type = (
                self._normalise(
                    port.port_type
                )
            )

            if normalized_port_type in {
                "p port",
                "p-port",
                "pport",
                "provided port",
                "provider port",
                "provided",
            }:

                if not interface_map[key][
                    "provider"
                ]:
                    interface_map[key][
                        "provider"
                    ] = component_name

            elif normalized_port_type in {
                "r port",
                "r-port",
                "rport",
                "required port",
                "receiver port",
                "required",
            }:

                if not interface_map[key][
                    "consumer"
                ]:
                    interface_map[key][
                        "consumer"
                    ] = component_name

        interfaces = [
            Interface(
                name=data["name"],
                provider=data["provider"],
                consumer=data["consumer"],
            )
            for data in interface_map.values()
        ]

        # ============================================
        # FINAL MODEL
        # ============================================

        return ArchitectureModel(
            filename=path.name,
            document_id=document_id,
            version=version,

            components=self._unique(
                components,
                "name",
            ),

            interfaces=self._unique(
                interfaces,
                "name",
            ),

            ports=self._unique(
                ports,
                "name",
            ),

            signals=self._unique(
                signals,
                "name",
            ),

            dependencies=(
                self._unique_dependencies(
                    dependencies
                )
            ),
        )

    # ================================================
    # HELPER METHODS
    # ================================================

    @staticmethod
    def _clean(value) -> str:

        if value is None:
            return ""

        return " ".join(
            str(value).split()
        ).strip()

    def _normalise(
        self,
        value,
    ) -> str:

        value = self._clean(
            value
        )

        value = value.lower()

        value = re.sub(
            r"[_/]+",
            " ",
            value,
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value.strip()

    def _canonical_header(
        self,
        value,
    ) -> str:

        normalized = (
            self._normalise(value)
        )

        return self.HEADER_ALIASES.get(
            normalized,
            normalized,
        )

    def _port_type(
        self,
        value,
    ) -> str:

        normalized = (
            self._normalise(value)
        )

        return self.PORT_TYPE_ALIASES.get(
            normalized,
            self._clean(value),
        )

    def _clean_table(
        self,
        table,
    ) -> list[list[str]]:

        cleaned = []

        for row in table:

            if row is None:
                continue

            cleaned_row = [
                self._clean(cell)
                for cell in row
            ]

            if any(cleaned_row):

                cleaned.append(
                    cleaned_row
                )

        return cleaned

    def _cell(
        self,
        row,
        index,
    ) -> str:

        if (
            index is None
            or index >= len(row)
        ):
            return ""

        return self._clean(
            row[index]
        )

    @staticmethod
    def _unique(
        items,
        attribute,
    ):

        unique = {}

        for item in items:

            key = getattr(
                item,
                attribute,
                "",
            )

            normalized_key = (
                key.strip().lower()
                if key
                else ""
            )

            if (
                normalized_key
                and normalized_key
                not in unique
            ):

                unique[
                    normalized_key
                ] = item

        return list(
            unique.values()
        )

    @staticmethod
    def _unique_dependencies(
        dependencies,
    ):

        unique = {}

        for item in dependencies:

            dependent = (
                item
                .dependent_component
                .strip()
            )

            required = (
                item
                .required_component
                .strip()
            )

            if (
                not dependent
                or not required
            ):
                continue

            key = (
                dependent.lower(),
                required.lower(),
            )

            if key not in unique:

                unique[key] = item

        return list(
            unique.values()
        )