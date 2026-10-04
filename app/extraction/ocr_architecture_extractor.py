import re
from pathlib import Path
from difflib import SequenceMatcher

from app.ingestion.pdf_parser import PDFParser
from app.models.architecture import (
    ArchitectureModel,
    Component,
    Interface,
    Port,
    Signal,
    Dependency,
)


class OCRArchitectureExtractor:
    """
    Extract structured architecture information from scanned HLD PDFs.

    Pipeline:
        Scanned PDF
        -> Tesseract OCR
        -> Numbered section detection
        -> Component extraction
        -> Interface extraction
        -> Port extraction
        -> Signal extraction
        -> Dependency extraction
        -> OCR normalization
        -> ArchitectureModel
    """

    def __init__(self):
        self.pdf_parser = PDFParser()

    # =========================================================
    # MAIN EXTRACTION
    # =========================================================

    def extract(self, file_path: str) -> ArchitectureModel:

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"PDF not found: {path}"
            )

        if path.suffix.lower() != ".pdf":
            raise ValueError(
                "OCR architecture extractor requires a PDF."
            )

        # -----------------------------------------------------
        # Parse PDF using the hybrid PDF/OCR parser
        # -----------------------------------------------------

        document = self.pdf_parser.parse(
            str(path)
        )

        text = document.full_text

        # -----------------------------------------------------
        # Metadata
        # -----------------------------------------------------

        document_id = self._extract_document_id(
            text
        )

        version = self._extract_version(
            text
        )

        # -----------------------------------------------------
        # Extract numbered HLD sections
        # -----------------------------------------------------

        component_section = self._section(
            text,
            "Software Components",
            "Interfaces",
        )

        interface_section = self._section(
            text,
            "Interfaces",
            "Port Definitions",
        )

        port_section = self._section(
            text,
            "Port Definitions",
            "Signal Definitions",
        )

        signal_section = self._section(
            text,
            "Signal Definitions",
            "Component Dependencies",
        )

        dependency_section = self._section(
            text,
            "Component Dependencies",
            "Functional Flow",
        )

        # -----------------------------------------------------
        # STEP 1: COMPONENTS
        #
        # The Software Components section is treated as the
        # authoritative source for component identity.
        # -----------------------------------------------------

        components = self._extract_components(
            component_section
        )

        component_names = [
            component.name
            for component in components
        ]

        # -----------------------------------------------------
        # STEP 2: INTERFACES
        # -----------------------------------------------------

        interfaces = self._extract_interfaces(
            interface_section,
            component_names,
        )

        interface_names = [
            interface.name
            for interface in interfaces
        ]

        # -----------------------------------------------------
        # STEP 3: PORTS
        # -----------------------------------------------------

        ports = self._extract_ports(
            port_section,
            component_names,
            interface_names,
        )

        # -----------------------------------------------------
        # STEP 4: SIGNALS
        # -----------------------------------------------------

        signals = self._extract_signals(
            signal_section,
            interface_names,
        )

        # -----------------------------------------------------
        # STEP 5: DEPENDENCIES
        # -----------------------------------------------------

        dependencies = self._extract_dependencies(
            dependency_section,
            component_names,
        )

        # -----------------------------------------------------
        # FINAL STRUCTURED MODEL
        # -----------------------------------------------------

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
            dependencies=self._unique_dependencies(
                dependencies
            ),
        )

    # =========================================================
    # METADATA EXTRACTION
    # =========================================================

    @staticmethod
    def _extract_document_id(
        text: str,
    ) -> str:

        patterns = [
            (
                r"Document\s+ID\s*\|?\s*"
                r"([A-Za-z0-9._\-]+)"
            ),
            (
                r"Document\s+identifier\s*:\s*"
                r"([A-Za-z0-9._\-]+)"
            ),
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if match:
                return match.group(1).strip()

        return ""

    @staticmethod
    def _extract_version(
        text: str,
    ) -> str:

        patterns = [
            (
                r"\bVersion\s*\|?\s*"
                r"([0-9]+(?:\.[0-9]+)*)"
            ),
            (
                r"Current\s+document\s+version\s*:\s*"
                r"([0-9]+(?:\.[0-9]+)*)"
            ),
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if match:
                return match.group(1).strip()

        return ""

    # =========================================================
    # SECTION EXTRACTION
    # =========================================================

    @staticmethod
    def _section(
        text: str,
        start_heading: str,
        end_heading: str,
    ) -> str:
        """
        Extract text between numbered HLD headings.

        Example:

            2. Software Components
            ...
            3. Interfaces

        The headings must appear at the beginning of a line.

        This prevents ordinary sentences such as:

            "defines software components, ports, interfaces..."

        from being incorrectly interpreted as section headings.
        """

        pattern = (
            rf"^\s*\d+\.\s*"
            rf"{re.escape(start_heading)}\s*$"
            rf"(.*?)"
            rf"(?=^\s*\d+\.\s*"
            rf"{re.escape(end_heading)}\s*$)"
        )

        match = re.search(
            pattern,
            text,
            flags=(
                re.IGNORECASE
                | re.MULTILINE
                | re.DOTALL
            ),
        )

        if not match:
            return ""

        return match.group(1).strip()

    # =========================================================
    # COMPONENT EXTRACTION
    # =========================================================

    def _extract_components(
        self,
        section: str,
    ) -> list[Component]:

        components = []

        for line in self._usable_lines(
            section
        ):

            lower = line.lower()

            # Ignore the table header.
            if (
                "component" in lower
                and "responsibility" in lower
            ):
                continue

            # OCR examples:
            #
            # WheelSpeedSensor Acquires wheel-speed information...
            #
            # VehicleSpeedController | Processes wheel-speed...
            #
            # InstrumentCluster Displays validated speed...
            #
            # The first identifier is therefore the component
            # name and the remaining text is its description.

            match = re.match(
                r"^\|?\s*"
                r"([A-Za-z][A-Za-z0-9_]*)"
                r"\s*(.*)$",
                line,
            )

            if not match:
                continue

            name = (
                match.group(1)
                .strip("|] ")
            )

            description = (
                match.group(2)
                .replace("|", " ")
                .replace("]", " ")
                .strip()
            )

            if not self._valid_component_candidate(
                name
            ):
                continue

            components.append(
                Component(
                    name=name,
                    description=description,
                )
            )

        return components

    # =========================================================
    # COMPONENT VALIDATION
    # =========================================================

    @staticmethod
    def _valid_component_candidate(
        value: str,
    ) -> bool:

        blocked = {
            "component",
            "responsibility",
            "prototype",
            "evaluation",
            "document",
            "page",
        }

        if not value:
            return False

        if value.lower() in blocked:
            return False

        if len(value) < 3:
            return False

        return True

    # =========================================================
    # INTERFACE EXTRACTION
    # =========================================================

    def _extract_interfaces(
        self,
        section: str,
        component_names: list[str],
    ) -> list[Interface]:

        interfaces = []

        for line in self._usable_lines(
            section
        ):

            lower = line.lower()

            # Ignore header.
            if (
                "interface" in lower
                and "provider" in lower
                and "consumer" in lower
            ):
                continue

            # -------------------------------------------------
            # Interface name
            # -------------------------------------------------

            interface_match = re.search(
                r"([A-Za-z][A-Za-z0-9_]*interface)",
                line,
                flags=re.IGNORECASE,
            )

            if not interface_match:
                continue

            interface_name = (
                self._canonical_interface(
                    interface_match.group(1)
                )
            )

            # -------------------------------------------------
            # Provider and consumer
            # -------------------------------------------------

            found_components = (
                self._entities_in_order(
                    line,
                    component_names,
                )
            )

            if len(found_components) < 2:
                continue

            interfaces.append(
                Interface(
                    name=interface_name,
                    provider=found_components[0],
                    consumer=found_components[1],
                )
            )

        return interfaces

    # =========================================================
    # PORT EXTRACTION
    # =========================================================

    def _extract_ports(
        self,
        section: str,
        component_names: list[str],
        interface_names: list[str],
    ) -> list[Port]:

        ports = []

        for line in self._usable_lines(
            section
        ):

            lower = line.lower()

            # Ignore table header.
            if (
                "component" in lower
                and "port" in lower
                and "interface" in lower
            ):
                continue

            # -------------------------------------------------
            # Detect P-Port / R-Port
            # -------------------------------------------------

            type_match = re.search(
                r"\b([PR])\s*-\s*Port\b",
                line,
                flags=re.IGNORECASE,
            )

            if not type_match:
                continue

            port_type = (
                type_match.group(1).upper()
                + "-Port"
            )

            # -------------------------------------------------
            # Component
            # -------------------------------------------------

            component = self._best_entity_match(
                line,
                component_names,
            )

            # -------------------------------------------------
            # Interface
            # -------------------------------------------------

            interface = self._best_entity_match(
                line,
                interface_names,
            )

            # OCR may produce:
            #
            # WheelSpeedinterface
            #
            # instead of:
            #
            # WheelSpeedInterface
            if not interface:

                raw_interface = re.search(
                    r"([A-Za-z][A-Za-z0-9_]*interface)",
                    line,
                    flags=re.IGNORECASE,
                )

                if raw_interface:

                    candidate = (
                        self._canonical_interface(
                            raw_interface.group(1)
                        )
                    )

                    interface = (
                        self._closest_name(
                            candidate,
                            interface_names,
                        )
                        or candidate
                    )

            if not component or not interface:
                continue

            # -------------------------------------------------
            # Extract port name
            # -------------------------------------------------

            component_match = re.search(
                re.escape(component),
                line,
                flags=re.IGNORECASE,
            )

            if not component_match:
                continue

            # Port name is located between the component
            # identifier and P-Port / R-Port.

            middle = line[
                component_match.end():
                type_match.start()
            ]

            middle = (
                middle
                .replace("|", " ")
                .replace("]", " ")
                .strip()
            )

            words = re.findall(
                r"[A-Za-z][A-Za-z0-9_]*",
                middle,
            )

            if not words:
                continue

            raw_port_name = words[-1]

            # -------------------------------------------------
            # Correct small OCR spelling errors
            # -------------------------------------------------

            port_name = self._canonical_port_name(
                raw_port_name,
                interface,
                port_type,
            )

            ports.append(
                Port(
                    component=component,
                    name=port_name,
                    port_type=port_type,
                    interface=interface,
                )
            )

        return ports

    # =========================================================
    # SIGNAL EXTRACTION
    # =========================================================

    def _extract_signals(
        self,
        section: str,
        interface_names: list[str],
    ) -> list[Signal]:

        signals = []

        for line in self._usable_lines(
            section
        ):

            lower = line.lower()

            # Ignore table header.
            if (
                "signal" in lower
                and "interface" in lower
                and "unit" in lower
            ):
                continue

            # -------------------------------------------------
            # Interface
            # -------------------------------------------------

            interface = self._best_entity_match(
                line,
                interface_names,
            )

            if not interface:

                raw_interface = re.search(
                    r"([A-Za-z][A-Za-z0-9_]*interface)",
                    line,
                    flags=re.IGNORECASE,
                )

                if raw_interface:

                    candidate = (
                        self._canonical_interface(
                            raw_interface.group(1)
                        )
                    )

                    interface = (
                        self._closest_name(
                            candidate,
                            interface_names,
                        )
                        or candidate
                    )

            if not interface:
                continue

            # -------------------------------------------------
            # Clean OCR separators
            # -------------------------------------------------

            cleaned = (
                line
                .replace("|", " ")
                .replace("]", " ")
                .strip()
            )

            words = re.findall(
                r"[A-Za-z][A-Za-z0-9_]*",
                cleaned,
            )

            if not words:
                continue

            # First meaningful identifier is signal name.
            signal_name = words[0]

            # -------------------------------------------------
            # Unit
            # -------------------------------------------------

            unit = ""

            unit_match = re.search(
                r"(km/h|m/s|rpm|degC|°C|V|A|%)",
                line,
                flags=re.IGNORECASE,
            )

            if unit_match:
                unit = unit_match.group(1)

            signals.append(
                Signal(
                    name=signal_name,
                    interface=interface,
                    unit=unit,
                )
            )

        return signals

    # =========================================================
    # DEPENDENCY EXTRACTION
    # =========================================================

    def _extract_dependencies(
        self,
        section: str,
        component_names: list[str],
    ) -> list[Dependency]:

        dependencies = []

        for line in self._usable_lines(
            section
        ):

            lower = line.lower()

            # Ignore table header.
            if (
                "dependent" in lower
                and "required" in lower
            ):
                continue

            # Find known component names in the same order
            # they appear in the OCR text.

            found_components = (
                self._entities_in_order(
                    line,
                    component_names,
                )
            )

            if len(found_components) < 2:
                continue

            dependencies.append(
                Dependency(
                    dependent_component=(
                        found_components[0]
                    ),
                    required_component=(
                        found_components[1]
                    ),
                )
            )

        return dependencies

    # =========================================================
    # ENTITY ORDER
    # =========================================================

    @staticmethod
    def _entities_in_order(
        line: str,
        entities: list[str],
    ) -> list[str]:

        found = []

        for entity in entities:

            match = re.search(
                re.escape(entity),
                line,
                flags=re.IGNORECASE,
            )

            if match:

                found.append(
                    (
                        match.start(),
                        entity,
                    )
                )

        # Sort according to occurrence in the OCR line.
        found.sort(
            key=lambda item: item[0]
        )

        return [
            entity
            for _, entity in found
        ]

    # =========================================================
    # FUZZY ENTITY MATCHING
    # =========================================================

    def _best_entity_match(
        self,
        line: str,
        entities: list[str],
    ) -> str:

        # -----------------------------------------------------
        # Exact / case-insensitive match first
        # -----------------------------------------------------

        direct = self._entities_in_order(
            line,
            entities,
        )

        if direct:
            return direct[0]

        # -----------------------------------------------------
        # Fuzzy fallback for small OCR spelling errors
        # -----------------------------------------------------

        words = re.findall(
            r"[A-Za-z][A-Za-z0-9_]*",
            line,
        )

        best_name = ""
        best_score = 0.0

        for word in words:

            for entity in entities:

                score = SequenceMatcher(
                    None,
                    word.lower(),
                    entity.lower(),
                ).ratio()

                if score > best_score:

                    best_score = score
                    best_name = entity

        # Avoid aggressive fuzzy correction.
        if best_score >= 0.82:
            return best_name

        return ""

    # =========================================================
    # CLOSEST CANONICAL NAME
    # =========================================================

    @staticmethod
    def _closest_name(
        value: str,
        candidates: list[str],
    ) -> str:

        best_name = ""
        best_score = 0.0

        for candidate in candidates:

            score = SequenceMatcher(
                None,
                value.lower(),
                candidate.lower(),
            ).ratio()

            if score > best_score:

                best_score = score
                best_name = candidate

        if best_score >= 0.80:
            return best_name

        return ""

    # =========================================================
    # INTERFACE NORMALIZATION
    # =========================================================

    @staticmethod
    def _canonical_interface(
        value: str,
    ) -> str:

        value = value.strip(
            " |]"
        )

        match = re.match(
            r"(.+?)interface$",
            value,
            flags=re.IGNORECASE,
        )

        if not match:
            return value

        # Example:
        #
        # WheelSpeedinterface
        #
        # ->
        #
        # WheelSpeedInterface

        return (
            match.group(1)
            + "Interface"
        )

    # =========================================================
    # PORT NORMALIZATION
    # =========================================================

    @staticmethod
    def _canonical_port_name(
        raw_name: str,
        interface: str,
        port_type: str,
    ) -> str:

        # Example:
        #
        # WheelSpeedInterface
        #
        # ->
        #
        # WheelSpeed

        base = re.sub(
            r"Interface$",
            "",
            interface,
            flags=re.IGNORECASE,
        )

        if port_type == "P-Port":
            suffix = "Out"
        else:
            suffix = "In"

        expected = base + suffix

        similarity = SequenceMatcher(
            None,
            raw_name.lower(),
            expected.lower(),
        ).ratio()

        # Repair small OCR errors such as:
        #
        # wheetSpeedOut
        #
        # ->
        #
        # WheelSpeedOut

        if similarity >= 0.70:
            return expected

        return raw_name

    # =========================================================
    # LINE CLEANING
    # =========================================================

    @staticmethod
    def _usable_lines(
        section: str,
    ) -> list[str]:

        result = []

        for line in section.splitlines():

            cleaned = " ".join(
                line.split()
            ).strip()

            if not cleaned:
                continue

            # Ignore page markers inserted by PDFParser.
            if re.match(
                r"^\[PAGE\s+\d+\]$",
                cleaned,
                flags=re.IGNORECASE,
            ):
                continue

            result.append(cleaned)

        return result

    # =========================================================
    # DEDUPLICATION
    # =========================================================

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
            )

            if key:
                unique[key] = item

        return list(
            unique.values()
        )

    @staticmethod
    def _unique_dependencies(
        dependencies,
    ):

        unique = {}

        for item in dependencies:

            key = (
                item.dependent_component,
                item.required_component,
            )

            unique[key] = item

        return list(
            unique.values()
        )