import json
from pathlib import Path

from app.extraction.pdf_architecture_extractor import (
    PDFArchitectureExtractor,
)
from app.validation.consistency_checker import (
    ConsistencyChecker,
)


GROUND_TRUTH_PATH = Path(
    "data/ground_truth/architecture_ground_truth.json"
)

HLD_DIRECTORY = Path(
    "data/sample_hlds"
)


# =========================================================
# BASIC METRICS
# =========================================================

def calculate_metrics(
    predicted,
    expected,
):
    predicted = set(predicted)
    expected = set(expected)

    true_positive = len(
        predicted & expected
    )

    false_positive = len(
        predicted - expected
    )

    false_negative = len(
        expected - predicted
    )

    precision = (
        true_positive
        / (true_positive + false_positive)
        if true_positive + false_positive > 0
        else 0.0
    )

    recall = (
        true_positive
        / (true_positive + false_negative)
        if true_positive + false_negative > 0
        else 0.0
    )

    f1 = (
        2 * precision * recall
        / (precision + recall)
        if precision + recall > 0
        else 0.0
    )

    return {
        "tp": true_positive,
        "fp": false_positive,
        "fn": false_negative,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


# =========================================================
# ENTITY NORMALIZATION
# =========================================================

def normalize(value):
    return str(value).strip().lower()


def component_set(architecture):
    return {
        normalize(component.name)
        for component
        in architecture.components
    }


def interface_set(architecture):
    return {
        normalize(interface.name)
        for interface
        in architecture.interfaces
    }


def port_set(architecture):
    return {
        (
            normalize(port.component),
            normalize(port.name),
            normalize(port.port_type),
            normalize(port.interface),
        )
        for port
        in architecture.ports
    }


def signal_set(architecture):
    return {
        (
            normalize(signal.name),
            normalize(signal.interface),
            normalize(signal.unit),
        )
        for signal
        in architecture.signals
    }


def dependency_set(architecture):
    return {
        (
            normalize(
                dependency.dependent_component
            ),
            normalize(
                dependency.required_component
            ),
        )
        for dependency
        in architecture.dependencies
    }


# =========================================================
# GROUND TRUTH NORMALIZATION
# =========================================================

def expected_components(data):
    return {
        normalize(item["name"])
        for item in data["components"]
    }


def expected_interfaces(data):
    return {
        normalize(item["name"])
        for item in data["interfaces"]
    }


def expected_ports(data):
    return {
        (
            normalize(item["component"]),
            normalize(item["name"]),
            normalize(item["type"]),
            normalize(item["interface"]),
        )
        for item in data["ports"]
    }


def expected_signals(data):
    return {
        (
            normalize(item["name"]),
            normalize(item["interface"]),
            normalize(item.get("unit", "")),
        )
        for item in data["signals"]
    }


def expected_dependencies(data):
    return {
        (
            normalize(item[0]),
            normalize(item[1]),
        )
        for item in data["dependencies"]
    }


# =========================================================
# ISSUE NORMALIZATION
# =========================================================

def predicted_issue_set(issues):
    return {
        (
            normalize(issue.issue_type),
            normalize(issue.entity),
        )
        for issue in issues
    }


def expected_issue_set(data):
    result = set()

    for issue in data.get(
        "known_issues",
        []
    ):
        issue_type = normalize(
            issue.get(
                "issue_type",
                issue.get(
                    "type",
                    "",
                ),
            )
        )

        entity = normalize(
            issue.get(
                "entity",
                issue.get(
                    "interface",
                    issue.get(
                        "signal",
                        "",
                    ),
                ),
            )
        )

        if issue_type:
            result.add(
                (
                    issue_type,
                    entity,
                )
            )

    return result


# =========================================================
# AGGREGATE COUNTERS
# =========================================================

def empty_counter():
    return {
        "tp": 0,
        "fp": 0,
        "fn": 0,
    }


def add_metrics(
    counter,
    metrics,
):
    counter["tp"] += metrics["tp"]
    counter["fp"] += metrics["fp"]
    counter["fn"] += metrics["fn"]


def finalize(counter):
    tp = counter["tp"]
    fp = counter["fp"]
    fn = counter["fn"]

    precision = (
        tp / (tp + fp)
        if tp + fp > 0
        else 0.0
    )

    recall = (
        tp / (tp + fn)
        if tp + fn > 0
        else 0.0
    )

    f1 = (
        2 * precision * recall
        / (precision + recall)
        if precision + recall > 0
        else 0.0
    )

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def print_metric(
    name,
    metric,
):
    print(
        f"{name:<15}"
        f"P={metric['precision']:.3f}  "
        f"R={metric['recall']:.3f}  "
        f"F1={metric['f1']:.3f}  "
        f"TP={metric['tp']}  "
        f"FP={metric['fp']}  "
        f"FN={metric['fn']}"
    )


# =========================================================
# MAIN EVALUATION
# =========================================================

def main():

    print("=" * 78)
    print(
        "AUTOSAR HLD ASSISTANT - "
        "NATIVE PDF EXTRACTION EVALUATION"
    )
    print("=" * 78)

    with open(
        GROUND_TRUTH_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        ground_truth = json.load(file)

    documents = ground_truth.get(
        "documents",
        {}
    )

    if not documents:
        raise RuntimeError(
            "No documents found in "
            "architecture_ground_truth.json"
        )

    extractor = (
        PDFArchitectureExtractor()
    )

    checker = ConsistencyChecker()

    totals = {
        "components": empty_counter(),
        "interfaces": empty_counter(),
        "ports": empty_counter(),
        "signals": empty_counter(),
        "dependencies": empty_counter(),
    }

    evaluated_documents = 0

    print(
        f"\nGround-truth documents: "
        f"{len(documents)}"
    )

    # -----------------------------------------------------
    # DOCUMENT-BY-DOCUMENT EVALUATION
    # -----------------------------------------------------

    for filename, expected in (
        documents.items()
    ):

        pdf_path = (
            HLD_DIRECTORY
            / filename
        )

        print("\n" + "-" * 78)
        print(
            f"DOCUMENT: {filename}"
        )
        print("-" * 78)

        if not pdf_path.exists():

            print(
                "SKIPPED: PDF file not found."
            )

            continue

        architecture = (
            extractor.extract(
                pdf_path
            )
        )

        evaluated_documents += 1

        metrics = {}

        metrics["components"] = (
            calculate_metrics(
                component_set(
                    architecture
                ),
                expected_components(
                    expected
                ),
            )
        )

        metrics["interfaces"] = (
            calculate_metrics(
                interface_set(
                    architecture
                ),
                expected_interfaces(
                    expected
                ),
            )
        )

        metrics["ports"] = (
            calculate_metrics(
                port_set(
                    architecture
                ),
                expected_ports(
                    expected
                ),
            )
        )

        metrics["signals"] = (
            calculate_metrics(
                signal_set(
                    architecture
                ),
                expected_signals(
                    expected
                ),
            )
        )

        metrics["dependencies"] = (
            calculate_metrics(
                dependency_set(
                    architecture
                ),
                expected_dependencies(
                    expected
                ),
            )
        )

        for category in totals:

            add_metrics(
                totals[category],
                metrics[category],
            )

            print_metric(
                category.capitalize(),
                metrics[category],
            )

        # -------------------------------------------------
        # VALIDATION OUTPUT
        # -------------------------------------------------

        issues = checker.validate(
            architecture
        )

        print(
            "\nDetected validation issues:"
        )

        if issues:

            for issue in issues:

                print(
                    f"  - "
                    f"{issue.issue_type} | "
                    f"{issue.entity}"
                )

        else:

            print("  None")

    # =====================================================
    # FINAL EXTRACTION RESULTS
    # =====================================================

    if evaluated_documents == 0:
        raise RuntimeError(
            "Evaluation failed: "
            "zero documents were evaluated."
        )

    print("\n" + "=" * 78)
    print(
        "AGGREGATED NATIVE PDF "
        "EXTRACTION RESULTS"
    )
    print("=" * 78)

    overall = empty_counter()

    final_metrics = {}

    for category, counter in (
        totals.items()
    ):

        metric = finalize(
            counter
        )

        final_metrics[
            category
        ] = metric

        print_metric(
            category.capitalize(),
            metric,
        )

        overall["tp"] += (
            counter["tp"]
        )

        overall["fp"] += (
            counter["fp"]
        )

        overall["fn"] += (
            counter["fn"]
        )

    overall_metric = finalize(
        overall
    )

    print("-" * 78)

    print_metric(
        "OVERALL MICRO",
        overall_metric,
    )

    print(
        f"\nDocuments evaluated: "
        f"{evaluated_documents}"
    )

    print(
        "\nNOTE: These metrics apply only "
        "to the current controlled synthetic "
        "AUTOSAR-style evaluation corpus."
    )

    print(
        "\nNATIVE PDF EXTRACTION "
        "EVALUATION PASSED"
    )


if __name__ == "__main__":
    main()
    