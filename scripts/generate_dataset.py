from pathlib import Path
import json

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


BASE_DIR = Path(__file__).resolve().parent.parent
PDF_DIR = BASE_DIR / "data" / "sample_hlds"
GT_DIR = BASE_DIR / "data" / "ground_truth"

PDF_DIR.mkdir(parents=True, exist_ok=True)
GT_DIR.mkdir(parents=True, exist_ok=True)


DOCUMENTS = [
    {
        "filename": "Vehicle_Control_HLD_v1.pdf",
        "title": "Vehicle Control System - High Level Design",
        "document_id": "HLD-VCS-001",
        "version": "1.0",
        "system": "Vehicle Control System",
        "components": [
            {
                "name": "WheelSpeedSensor",
                "description": "Acquires wheel-speed information and provides vehicle speed data.",
            },
            {
                "name": "VehicleSpeedController",
                "description": "Processes wheel-speed information and calculates validated vehicle speed.",
            },
            {
                "name": "InstrumentCluster",
                "description": "Displays validated vehicle speed to the driver.",
            },
        ],
        "interfaces": [
            {
                "name": "WheelSpeedInterface",
                "provider": "WheelSpeedSensor",
                "consumer": "VehicleSpeedController",
            },
            {
                "name": "VehicleSpeedInterface",
                "provider": "VehicleSpeedController",
                "consumer": "InstrumentCluster",
            },
        ],
        "ports": [
            {
                "component": "WheelSpeedSensor",
                "name": "WheelSpeedOut",
                "type": "P-Port",
                "interface": "WheelSpeedInterface",
            },
            {
                "component": "VehicleSpeedController",
                "name": "WheelSpeedIn",
                "type": "R-Port",
                "interface": "WheelSpeedInterface",
            },
            {
                "component": "VehicleSpeedController",
                "name": "VehicleSpeedOut",
                "type": "P-Port",
                "interface": "VehicleSpeedInterface",
            },
            {
                "component": "InstrumentCluster",
                "name": "VehicleSpeedIn",
                "type": "R-Port",
                "interface": "VehicleSpeedInterface",
            },
        ],
        "signals": [
            {
                "name": "WheelSpeed",
                "interface": "WheelSpeedInterface",
                "unit": "km/h",
            },
            {
                "name": "VehicleSpeed",
                "interface": "VehicleSpeedInterface",
                "unit": "km/h",
            },
        ],
        "dependencies": [
            ["VehicleSpeedController", "WheelSpeedSensor"],
            ["InstrumentCluster", "VehicleSpeedController"],
        ],
        "known_issues": [],
    },

    {
        "filename": "Vehicle_Control_HLD_v2.pdf",
        "title": "Vehicle Control System - High Level Design",
        "document_id": "HLD-VCS-001",
        "version": "2.0",
        "system": "Vehicle Control System",
        "components": [
            {
                "name": "WheelSpeedSensor",
                "description": "Acquires wheel-speed information.",
            },
            {
                "name": "VehicleSpeedController",
                "description": "Processes wheel-speed information and calculates validated vehicle speed.",
            },
            {
                "name": "InstrumentCluster",
                "description": "Displays validated vehicle speed.",
            },
            {
                "name": "DiagnosticsManager",
                "description": "Monitors vehicle-speed plausibility and diagnostic status.",
            },
        ],
        "interfaces": [
            {
                "name": "WheelSpeedInterface",
                "provider": "WheelSpeedSensor",
                "consumer": "VehicleSpeedController",
            },
            {
                "name": "VehicleSpeedInterface",
                "provider": "VehicleSpeedController",
                "consumer": "InstrumentCluster",
            },
            {
                "name": "DiagnosticStatusInterface",
                "provider": "VehicleSpeedController",
                "consumer": "DiagnosticsManager",
            },
        ],
        "ports": [
            {
                "component": "WheelSpeedSensor",
                "name": "WheelSpeedOut",
                "type": "P-Port",
                "interface": "WheelSpeedInterface",
            },
            {
                "component": "VehicleSpeedController",
                "name": "WheelSpeedIn",
                "type": "R-Port",
                "interface": "WheelSpeedInterface",
            },
            {
                "component": "VehicleSpeedController",
                "name": "VehicleSpeedOut",
                "type": "P-Port",
                "interface": "VehicleSpeedInterface",
            },
            {
                "component": "InstrumentCluster",
                "name": "VehicleSpeedIn",
                "type": "R-Port",
                "interface": "VehicleSpeedInterface",
            },
            {
                "component": "DiagnosticsManager",
                "name": "DiagnosticStatusIn",
                "type": "R-Port",
                "interface": "DiagnosticStatusInterface",
            },
        ],
        "signals": [
            {
                "name": "Wheel_Speed",
                "interface": "WheelSpeedInterface",
                "unit": "km/h",
            },
            {
                "name": "VehicleSpeed",
                "interface": "VehicleSpeedInterface",
                "unit": "km/h",
            },
            {
                "name": "DiagnosticStatus",
                "interface": "DiagnosticStatusInterface",
                "unit": "enum",
            },
        ],
        "dependencies": [
            ["VehicleSpeedController", "WheelSpeedSensor"],
            ["InstrumentCluster", "VehicleSpeedController"],
            ["DiagnosticsManager", "VehicleSpeedController"],
        ],
        "known_issues": [
            {
                "issue_id": "VCS-V2-001",
                "type": "signal_revision_mismatch",
                "description": (
                    "WheelSpeed in version 1.0 is named Wheel_Speed "
                    "in version 2.0."
                ),
                "severity": "medium",
            },
            {
                "issue_id": "VCS-V2-002",
                "type": "missing_provider_port",
                "description": (
                    "DiagnosticStatusInterface is consumed by DiagnosticsManager "
                    "but no corresponding provider P-Port is declared."
                ),
                "severity": "high",
            },
        ],
    },

    {
        "filename": "Braking_System_HLD.pdf",
        "title": "Braking System - High Level Design",
        "document_id": "HLD-BRK-001",
        "version": "1.0",
        "system": "Braking System",
        "components": [
            {
                "name": "BrakePedalSensor",
                "description": "Measures brake-pedal demand.",
            },
            {
                "name": "BrakeController",
                "description": "Calculates requested braking command.",
            },
            {
                "name": "BrakeActuator",
                "description": "Executes the braking command.",
            },
        ],
        "interfaces": [
            {
                "name": "BrakePedalInterface",
                "provider": "BrakePedalSensor",
                "consumer": "BrakeController",
            },
            {
                "name": "BrakeCommandInterface",
                "provider": "BrakeController",
                "consumer": "BrakeActuator",
            },
        ],
        "ports": [
            {
                "component": "BrakePedalSensor",
                "name": "BrakePedalOut",
                "type": "P-Port",
                "interface": "BrakePedalInterface",
            },
            {
                "component": "BrakeController",
                "name": "BrakePedalIn",
                "type": "R-Port",
                "interface": "BrakePedalInterface",
            },
            {
                "component": "BrakeController",
                "name": "BrakeCommandOut",
                "type": "P-Port",
                "interface": "BrakeCommandInterface",
            },
            {
                "component": "BrakeActuator",
                "name": "BrakeCommandIn",
                "type": "R-Port",
                "interface": "BrakeCommandInterface",
            },
        ],
        "signals": [
            {
                "name": "BrakePedalPosition",
                "interface": "BrakePedalInterface",
                "unit": "%",
            },
            {
                "name": "BrakeCommand",
                "interface": "BrakeCommandInterface",
                "unit": "%",
            },
        ],
        "dependencies": [
            ["BrakeController", "BrakePedalSensor"],
            ["BrakeActuator", "BrakeController"],
        ],
        "known_issues": [],
    },

    {
        "filename": "Door_Control_HLD.pdf",
        "title": "Door Control System - High Level Design",
        "document_id": "HLD-DOOR-001",
        "version": "1.0",
        "system": "Door Control System",
        "components": [
            {
                "name": "DoorSwitch",
                "description": "Provides the driver door-lock request.",
            },
            {
                "name": "DoorController",
                "description": "Processes door-lock requests.",
            },
            {
                "name": "DoorLockActuator",
                "description": "Controls physical door locking.",
            },
        ],
        "interfaces": [
            {
                "name": "DoorRequestInterface",
                "provider": "DoorSwitch",
                "consumer": "DoorController",
            },
            {
                "name": "DoorLockInterface",
                "provider": "DoorController",
                "consumer": "DoorLockActuator",
            },
        ],
        "ports": [
            {
                "component": "DoorSwitch",
                "name": "DoorRequestOut",
                "type": "P-Port",
                "interface": "DoorRequestInterface",
            },
            {
                "component": "DoorController",
                "name": "DoorRequestIn",
                "type": "R-Port",
                "interface": "DoorRequestInterface",
            },
            {
                "component": "DoorLockActuator",
                "name": "DoorLockCommandIn",
                "type": "R-Port",
                "interface": "DoorLockInterface",
            },
        ],
        "signals": [
            {
                "name": "DoorLockRequest",
                "interface": "DoorRequestInterface",
                "unit": "boolean",
            },
            {
                "name": "DoorLockCommand",
                "interface": "DoorLockInterface",
                "unit": "boolean",
            },
        ],
        "dependencies": [
            ["DoorController", "DoorSwitch"],
            ["DoorLockActuator", "DoorController"],
        ],
        "known_issues": [
            {
                "issue_id": "DOOR-001",
                "type": "missing_provider_port",
                "description": (
                    "DoorLockInterface is consumed by DoorLockActuator but "
                    "DoorController has no declared provider P-Port for it."
                ),
                "severity": "high",
            }
        ],
    },

    {
        "filename": "Body_Control_HLD.pdf",
        "title": "Body Control System - High Level Design",
        "document_id": "HLD-BCM-001",
        "version": "1.0",
        "system": "Body Control System",
        "components": [
            {
                "name": "LightSwitch",
                "description": "Provides lighting requests.",
            },
            {
                "name": "BodyControlManager",
                "description": "Coordinates body-electronics functions.",
            },
            {
                "name": "ExteriorLightController",
                "description": "Controls exterior vehicle lights.",
            },
        ],
        "interfaces": [
            {
                "name": "LightRequestInterface",
                "provider": "LightSwitch",
                "consumer": "BodyControlManager",
            },
            {
                "name": "ExteriorLightInterface",
                "provider": "BodyControlManager",
                "consumer": "ExteriorLightController",
            },
        ],
        "ports": [
            {
                "component": "LightSwitch",
                "name": "LightRequestOut",
                "type": "P-Port",
                "interface": "LightRequestInterface",
            },
            {
                "component": "BodyControlManager",
                "name": "LightRequestIn",
                "type": "R-Port",
                "interface": "LightRequestInterface",
            },
            {
                "component": "BodyControlManager",
                "name": "ExteriorLightOut",
                "type": "P-Port",
                "interface": "ExteriorLightInterface",
            },
            {
                "component": "ExteriorLightController",
                "name": "ExteriorLightIn",
                "type": "R-Port",
                "interface": "ExteriorLightInterface",
            },
        ],
        "signals": [
            {
                "name": "LightRequest",
                "interface": "LightRequestInterface",
                "unit": "enum",
            },
            {
                "name": "ExteriorLightCommand",
                "interface": "ExteriorLightInterface",
                "unit": "enum",
            },
        ],
        "dependencies": [
            ["BodyControlManager", "LightSwitch"],
            ["ExteriorLightController", "BodyControlManager"],
        ],
        "known_issues": [],
    },
]


def make_styles():
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="DocumentTitle",
            parent=styles["Title"],
            alignment=TA_CENTER,
            spaceAfter=14,
        )
    )

    return styles


def add_table(story, headers, rows):
    data = [headers] + rows

    table = Table(
        data,
        repeatRows=1,
        hAlign="LEFT",
    )

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
            ]
        )
    )

    story.append(table)
    story.append(Spacer(1, 8 * mm))


def build_pdf(spec):
    path = PDF_DIR / spec["filename"]

    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=spec["title"],
        author="Synthetic AUTOSAR HLD Evaluation Corpus",
    )

    styles = make_styles()
    story = []

    story.append(
        Paragraph(
            spec["title"],
            styles["DocumentTitle"],
        )
    )

    story.append(
        Paragraph(
            "<b>Prototype Evaluation Document - Synthetic Data</b>",
            styles["Normal"],
        )
    )

    story.append(Spacer(1, 5 * mm))

    metadata_rows = [
        ["Document ID", spec["document_id"]],
        ["Version", spec["version"]],
        ["System", spec["system"]],
        ["Classification", "Synthetic / Evaluation Only"],
    ]

    add_table(
        story,
        ["Field", "Value"],
        metadata_rows,
    )

    story.append(
        Paragraph(
            "1. Purpose",
            styles["Heading1"],
        )
    )

    story.append(
        Paragraph(
            f"This High Level Design describes the software architecture "
            f"of the {spec['system']}. The document defines software "
            f"components, ports, interfaces, signals, dependencies and "
            f"high-level functional flow for prototype evaluation.",
            styles["BodyText"],
        )
    )

    story.append(Spacer(1, 5 * mm))

    story.append(
        Paragraph(
            "2. Software Components",
            styles["Heading1"],
        )
    )

    component_rows = [
        [item["name"], item["description"]]
        for item in spec["components"]
    ]

    add_table(
        story,
        ["Component", "Responsibility"],
        component_rows,
    )

    story.append(
        Paragraph(
            "3. Interfaces",
            styles["Heading1"],
        )
    )

    interface_rows = [
        [
            item["name"],
            item["provider"],
            item["consumer"],
        ]
        for item in spec["interfaces"]
    ]

    add_table(
        story,
        ["Interface", "Provider", "Consumer"],
        interface_rows,
    )

    story.append(PageBreak())

    story.append(
        Paragraph(
            "4. Port Definitions",
            styles["Heading1"],
        )
    )

    port_rows = [
        [
            item["component"],
            item["name"],
            item["type"],
            item["interface"],
        ]
        for item in spec["ports"]
    ]

    add_table(
        story,
        ["Component", "Port", "Port Type", "Interface"],
        port_rows,
    )

    story.append(
        Paragraph(
            "5. Signal Definitions",
            styles["Heading1"],
        )
    )

    signal_rows = [
        [
            item["name"],
            item["interface"],
            item["unit"],
        ]
        for item in spec["signals"]
    ]

    add_table(
        story,
        ["Signal", "Interface", "Unit"],
        signal_rows,
    )

    story.append(
        Paragraph(
            "6. Component Dependencies",
            styles["Heading1"],
        )
    )

    dependency_rows = [
        [consumer, provider]
        for consumer, provider in spec["dependencies"]
    ]

    add_table(
        story,
        ["Dependent Component", "Required Component"],
        dependency_rows,
    )

    story.append(
        Paragraph(
            "7. Functional Flow",
            styles["Heading1"],
        )
    )

    flow = " -> ".join(
        component["name"]
        for component in spec["components"]
    )

    story.append(
        Paragraph(
            flow,
            styles["BodyText"],
        )
    )

    story.append(Spacer(1, 5 * mm))

    story.append(
        Paragraph(
            "8. Revision Information",
            styles["Heading1"],
        )
    )

    story.append(
        Paragraph(
            f"Current document version: {spec['version']}. "
            f"Document identifier: {spec['document_id']}.",
            styles["BodyText"],
        )
    )

    doc.build(story)

    print(f"Created: {path.name}")


def create_ground_truth():
    ground_truth = {
        "dataset_name": "Synthetic AUTOSAR HLD Evaluation Corpus",
        "purpose": (
            "Controlled evaluation data for the AUTOSAR HLD "
            "Document Analysis Assistant."
        ),
        "documents": {},
    }

    for spec in DOCUMENTS:
        ground_truth["documents"][spec["filename"]] = {
            "document_id": spec["document_id"],
            "version": spec["version"],
            "system": spec["system"],
            "components": spec["components"],
            "interfaces": spec["interfaces"],
            "ports": spec["ports"],
            "signals": spec["signals"],
            "dependencies": spec["dependencies"],
            "known_issues": spec["known_issues"],
        }

    output = GT_DIR / "architecture_ground_truth.json"

    with output.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            ground_truth,
            file,
            indent=2,
        )

    print(f"Created: {output.name}")


def main():
    print("\nGenerating synthetic HLD evaluation corpus...\n")

    for document in DOCUMENTS:
        build_pdf(document)

    create_ground_truth()

    print("\nDataset generation complete.")


if __name__ == "__main__":
    main()