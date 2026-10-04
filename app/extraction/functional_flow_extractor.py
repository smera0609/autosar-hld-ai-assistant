import re
from pathlib import Path

from app.ingestion.pdf_parser import PDFParser


class FunctionalFlowExtractor:
    """
    Extract high-level functional flows from an AUTOSAR-style HLD.

    Example HLD text:

        WheelSpeedSensor
            -> VehicleSpeedController
            -> InstrumentCluster

    Result:

        {
            "flow_text": "...",
            "nodes": [
                "WheelSpeedSensor",
                "VehicleSpeedController",
                "InstrumentCluster"
            ],
            "edges": [
                ("WheelSpeedSensor", "VehicleSpeedController"),
                ("VehicleSpeedController", "InstrumentCluster")
            ]
        }
    """

    def __init__(self):
        self.parser = PDFParser()

    def extract(self, file_path: str) -> dict:

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"HLD file not found: {file_path}"
            )

        document = self.parser.parse(
            str(path)
        )

        section = self._extract_flow_section(
            document.full_text
        )

        if not section:
            return {
                "filename": path.name,
                "flow_text": "",
                "nodes": [],
                "edges": [],
            }

        flow_text = self._find_flow_expression(
            section
        )

        if not flow_text:
            return {
                "filename": path.name,
                "flow_text": "",
                "nodes": [],
                "edges": [],
            }

        nodes = self._extract_nodes(
            flow_text
        )

        edges = [
            (nodes[i], nodes[i + 1])
            for i in range(len(nodes) - 1)
        ]

        return {
            "filename": path.name,
            "flow_text": flow_text,
            "nodes": nodes,
            "edges": edges,
        }

    @staticmethod
    def _extract_flow_section(
        text: str,
    ) -> str:
        """
        Extract only the numbered Functional Flow section.

        This prevents occurrences of the words
        'functional flow' in the Purpose section from
        being incorrectly selected.
        """

        pattern = (
            r"^\s*\d+\.\s*"
            r"Functional\s+Flow\s*$"
            r"(.*?)"
            r"(?=^\s*\d+\.\s*"
            r"Revision\s+Information\s*$|\Z)"
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

    @staticmethod
    def _find_flow_expression(
        section: str,
    ) -> str:
        """
        Find a line containing an arrow-based functional flow.
        """

        for line in section.splitlines():

            line = line.strip()

            if "->" in line:
                return line

        # Support a flow broken across lines.
        compact = " ".join(
            line.strip()
            for line in section.splitlines()
            if line.strip()
        )

        if "->" in compact:
            return compact

        return ""

    @staticmethod
    def _extract_nodes(
        flow_text: str,
    ) -> list[str]:
        """
        Split:

            A -> B -> C

        into:

            ["A", "B", "C"]
        """

        raw_nodes = re.split(
            r"\s*->\s*",
            flow_text
        )

        nodes = []

        for node in raw_nodes:

            cleaned = (
                node
                .replace("|", "")
                .replace("]", "")
                .strip()
            )

            # Keep architecture-style identifiers.
            match = re.search(
                r"[A-Za-z][A-Za-z0-9_]*",
                cleaned
            )

            if match:
                nodes.append(
                    match.group(0)
                )

        return nodes
    