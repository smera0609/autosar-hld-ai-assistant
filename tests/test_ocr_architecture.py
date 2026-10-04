import json
from pathlib import Path

from app.extraction.ocr_architecture_extractor import (
    OCRArchitectureExtractor,
)


GROUND_TRUTH_PATH = Path(
    "data/ground_truth/architecture_ground_truth.json"
)

SCANNED_DIR = Path(
    "data/sample_hlds"
)

SCANNED_FILES = {
    "Vehicle_Control_HLD_v1.pdf":
        "Vehicle_Control_HLD_v1_SCANNED.pdf",

    "Vehicle_Control_HLD_v2.pdf":
        "Vehicle_Control_HLD_v2_SCANNED.pdf",

    "Braking_System_HLD.pdf":
        "Braking_System_HLD_SCANNED.pdf",

    "Door_Control_HLD.pdf":
        "Door_Control_HLD_SCANNED.pdf",

    "Body_Control_HLD.pdf":
        "Body_Control_HLD_SCANNED.pdf",
}


# ============================================================
# NORMALIZATION
# ============================================================

def normalize(value):
    return str(value).strip().lower()


# ============================================================
# METRICS
# ============================================================

def calculate_metrics(predicted, expected):

    predicted = set(predicted)
    expected = set(expected)

    tp = len(predicted & expected)
    fp = len(predicted - expected)
    fn = len(expected - predicted)

    precision = (
        tp / (tp + fp)
        if (tp + fp) > 0
        else None
    )

    recall = (
        tp / (tp + fn)
        if (tp + fn) > 0
        else None
    )

    if (
        precision is not None
        and recall is not None
        and (precision + recall) > 0
    ):
        f1 = (
            2 * precision * recall
            / (precision + recall)
        )
    else:
        f1 = None

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def format_score(value):

    if value is None:
        return "N/A"

    return f"{value:.3f}"


def print_metric(name, metric):

    print(
        f"{name:<14}"
        f"P={format_score(metric['precision']):<6} "
        f"R={format_score(metric['recall']):<6} "
        f"F1={format_score(metric['f1']):<6} "
        f"TP={metric['tp']}  "
        f"FP={metric['fp']}  "
        f"FN={metric['fn']}"
    )


def print_difference(
    name,
    predicted,
    expected,
):

    extra = predicted - expected
    missing = expected - predicted

    if extra:
        print(
            f"  EXTRA {name}: "
            f"{sorted(extra)}"
        )

    if missing:
        print(
            f"  MISSING {name}: "
            f"{sorted(missing)}"
        )


# ============================================================
# EXPECTED VALUES
# ============================================================

def get_expected(data):

    components = {
        normalize(item["name"])
        for item in data.get(
            "components",
            []
        )
    }

    interfaces = {
        normalize(item["name"])
        for item in data.get(
            "interfaces",
            []
        )
    }

    ports = {
        normalize(item["name"])
        for item in data.get(
            "ports",
            []
        )
    }

    signals = {
        normalize(item["name"])
        for item in data.get(
            "signals",
            []
        )
    }

    dependencies = {
        (
            normalize(item[0]),
            normalize(item[1]),
        )
        for item in data.get(
            "dependencies",
            []
        )
        if len(item) >= 2
    }

    return {
        "components": components,
        "interfaces": interfaces,
        "ports": ports,
        "signals": signals,
        "dependencies": dependencies,
    }


# ============================================================
# PREDICTED VALUES
# ============================================================

def get_predicted(model):

    components = {
        normalize(item.name)
        for item in model.components
    }

    interfaces = {
        normalize(item.name)
        for item in model.interfaces
    }

    ports = {
        normalize(item.name)
        for item in model.ports
    }

    signals = {
        normalize(item.name)
        for item in model.signals
    }

    dependencies = {
        (
            normalize(
                item.dependent_component
            ),
            normalize(
                item.required_component
            ),
        )
        for item in model.dependencies
    }

    return {
        "components": components,
        "interfaces": interfaces,
        "ports": ports,
        "signals": signals,
        "dependencies": dependencies,
    }


# ============================================================
# MAIN EVALUATION
# ============================================================

def main():

    if not GROUND_TRUTH_PATH.exists():
        raise FileNotFoundError(
            f"Ground truth not found: "
            f"{GROUND_TRUTH_PATH}"
        )

    with open(
        GROUND_TRUTH_PATH,
        "r",
        encoding="utf-8",
    ) as file:

        root = json.load(file)

    documents = root.get(
        "documents"
    )

    if not isinstance(
        documents,
        dict,
    ):
        raise ValueError(
            "Ground truth must contain "
            "a 'documents' dictionary."
        )

    extractor = (
        OCRArchitectureExtractor()
    )

    entity_types = [
        "components",
        "interfaces",
        "ports",
        "signals",
        "dependencies",
    ]

    aggregate = {
        entity_type: {
            "predicted": set(),
            "expected": set(),
        }
        for entity_type
        in entity_types
    }

    evaluated = 0
    failed = 0

    print()
    print("=" * 78)
    print(
        "OCR ARCHITECTURE EXTRACTION EVALUATION"
    )
    print("=" * 78)

    print(
        f"Dataset: "
        f"{root.get('dataset_name', 'Unknown')}"
    )

    print(
        f"Ground-truth documents: "
        f"{len(documents)}"
    )

    # ========================================================
    # PROCESS EACH DOCUMENT
    # ========================================================

    for (
        original_filename,
        scanned_filename,
    ) in SCANNED_FILES.items():

        print()
        print("-" * 78)
        print(
            f"DOCUMENT: {scanned_filename}"
        )
        print("-" * 78)

        if original_filename not in documents:

            print(
                "[ERROR] Missing ground truth."
            )

            failed += 1
            continue

        scanned_path = (
            SCANNED_DIR
            / scanned_filename
        )

        if not scanned_path.exists():

            print(
                f"[ERROR] Missing scanned PDF: "
                f"{scanned_path}"
            )

            failed += 1
            continue

        try:

            model = extractor.extract(
                str(scanned_path)
            )

        except Exception as error:

            print(
                f"[ERROR] Extraction failed: "
                f"{error}"
            )

            failed += 1
            continue

        evaluated += 1

        expected_data = (
            documents[
                original_filename
            ]
        )

        expected = get_expected(
            expected_data
        )

        predicted = get_predicted(
            model
        )

        # ----------------------------------------------------
        # Metadata
        # ----------------------------------------------------

        print(
            f"Document ID : "
            f"{model.document_id}"
        )

        print(
            f"Version     : "
            f"{model.version}"
        )

        id_correct = (
            normalize(
                model.document_id
            )
            ==
            normalize(
                expected_data.get(
                    "document_id",
                    "",
                )
            )
        )

        version_correct = (
            normalize(
                model.version
            )
            ==
            normalize(
                expected_data.get(
                    "version",
                    "",
                )
            )
        )

        print(
            f"ID correct  : "
            f"{id_correct}"
        )

        print(
            f"Version OK  : "
            f"{version_correct}"
        )

        print()

        # ----------------------------------------------------
        # Per-document evaluation
        # ----------------------------------------------------

        for entity_type in entity_types:

            metric = calculate_metrics(
                predicted[
                    entity_type
                ],
                expected[
                    entity_type
                ],
            )

            print_metric(
                entity_type.capitalize(),
                metric,
            )

            print_difference(
                entity_type.upper(),
                predicted[
                    entity_type
                ],
                expected[
                    entity_type
                ],
            )

            # -----------------------------------------------
            # Add document name to prevent identical entity
            # names from collapsing across documents.
            # -----------------------------------------------

            for value in predicted[
                entity_type
            ]:

                aggregate[
                    entity_type
                ][
                    "predicted"
                ].add(
                    (
                        original_filename,
                        value,
                    )
                )

            for value in expected[
                entity_type
            ]:

                aggregate[
                    entity_type
                ][
                    "expected"
                ].add(
                    (
                        original_filename,
                        value,
                    )
                )

    # ========================================================
    # STATUS
    # ========================================================

    print()
    print("=" * 78)
    print(
        "EVALUATION STATUS"
    )
    print("=" * 78)

    print(
        f"Evaluated documents : "
        f"{evaluated}"
    )

    print(
        f"Failed/skipped      : "
        f"{failed}"
    )

    # Prevent false 100% results.
    if evaluated == 0:

        print()
        print(
            "ERROR: No documents were evaluated."
        )

        print(
            "Metrics will not be reported."
        )

        return

    # ========================================================
    # AGGREGATE METRICS
    # ========================================================

    print()
    print("=" * 78)
    print(
        "AGGREGATE OCR EXTRACTION RESULTS"
    )
    print("=" * 78)

    aggregate_metrics = {}

    for entity_type in entity_types:

        metric = calculate_metrics(
            aggregate[
                entity_type
            ][
                "predicted"
            ],
            aggregate[
                entity_type
            ][
                "expected"
            ],
        )

        aggregate_metrics[
            entity_type
        ] = metric

        print_metric(
            entity_type.capitalize(),
            metric,
        )

    # ========================================================
    # MICRO AVERAGE
    # ========================================================

    total_tp = sum(
        metric["tp"]
        for metric
        in aggregate_metrics.values()
    )

    total_fp = sum(
        metric["fp"]
        for metric
        in aggregate_metrics.values()
    )

    total_fn = sum(
        metric["fn"]
        for metric
        in aggregate_metrics.values()
    )

    if (
        total_tp
        + total_fp
        + total_fn
        == 0
    ):

        print()
        print(
            "ERROR: No entities were evaluated."
        )

        return

    overall_precision = (
        total_tp
        / (total_tp + total_fp)
        if (total_tp + total_fp)
        else 0.0
    )

    overall_recall = (
        total_tp
        / (total_tp + total_fn)
        if (total_tp + total_fn)
        else 0.0
    )

    overall_f1 = (
        2
        * overall_precision
        * overall_recall
        / (
            overall_precision
            + overall_recall
        )
        if (
            overall_precision
            + overall_recall
        )
        else 0.0
    )

    print()
    print("-" * 78)
    print(
        "OVERALL MICRO-AVERAGE"
    )

    print(
        f"Precision : "
        f"{overall_precision:.3f}"
    )

    print(
        f"Recall    : "
        f"{overall_recall:.3f}"
    )

    print(
        f"F1        : "
        f"{overall_f1:.3f}"
    )

    print(
        f"TP={total_tp}  "
        f"FP={total_fp}  "
        f"FN={total_fn}"
    )

    print("=" * 78)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
    