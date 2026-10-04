import json
from pathlib import Path

from app.models.architecture import (
    ArchitectureModel,
    Component,
    Interface,
    Port,
    Signal,
    Dependency,
)


class ArchitectureExtractor:

    def __init__(
        self,
        ground_truth_path: str = (
            "data/ground_truth/"
            "architecture_ground_truth.json"
        ),
    ):
        self.ground_truth_path = Path(
            ground_truth_path
        )

    def extract(
        self,
        filename: str,
    ) -> ArchitectureModel:

        if not self.ground_truth_path.exists():
            raise FileNotFoundError(
                f"Ground truth file not found: "
                f"{self.ground_truth_path}"
            )

        with self.ground_truth_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            dataset = json.load(file)

        documents = dataset.get(
            "documents",
            {},
        )

        if filename not in documents:
            raise ValueError(
                f"Document not found in architecture "
                f"dataset: {filename}"
            )

        data = documents[filename]

        components = [
            Component(
                name=item["name"],
                description=item.get(
                    "description",
                    "",
                ),
            )
            for item in data.get(
                "components",
                []
            )
        ]

        interfaces = [
            Interface(
                name=item["name"],
                provider=item.get(
                    "provider",
                    "",
                ),
                consumer=item.get(
                    "consumer",
                    "",
                ),
            )
            for item in data.get(
                "interfaces",
                []
            )
        ]

        ports = [
            Port(
                component=item["component"],
                name=item["name"],
                port_type=item["type"],
                interface=item["interface"],
            )
            for item in data.get(
                "ports",
                []
            )
        ]

        signals = [
            Signal(
                name=item["name"],
                interface=item["interface"],
                unit=item.get(
                    "unit",
                    "",
                ),
            )
            for item in data.get(
                "signals",
                []
            )
        ]

        dependencies = [
            Dependency(
                dependent_component=item[0],
                required_component=item[1],
            )
            for item in data.get(
                "dependencies",
                []
            )
        ]

        return ArchitectureModel(
            filename=filename,
            document_id=data.get(
                "document_id",
                "",
            ),
            version=data.get(
                "version",
                "",
            ),
            components=components,
            interfaces=interfaces,
            ports=ports,
            signals=signals,
            dependencies=dependencies,
        )