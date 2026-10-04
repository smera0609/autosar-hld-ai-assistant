import json
import re
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
# NORMALIZATION
# =========================================================

def normalize(value):
    return str(value).strip().lower()


# =========================================================
# EXTRACT ENTITY FROM GROUND-TRUTH DESCRIPTION
# =========================================================

def extract_issue_entity(issue):
    """
    Ground-truth issues currently store the affected
    architecture entity inside the description rather
    than in a dedicated entity field.

    Example:

    DiagnosticStatusInterface is consumed by
    DiagnosticsManager but no corresponding provider
    P-Port is declared.

    -> DiagnosticStatusInterface
    """

    description = issue.get(
        "description",
        "",
    ).strip()

    issue_type = normalize(
        issue.get(
            "type",
            "",
        )
    )

    if not description:
        return ""

    # -----------------------------------------------------
    # MISSING PROVIDER / CONSUMER PORT
    # -----------------------------------------------------

    if issue_type in {
        "missing_provider_port",
        "missing_consumer_port",
    }:

        match = re.search(
            r"\b([A-Za-z][A-Za-z0-9_]*Interface)\b",
            description,
        )

        if match:
            return normalize(
                match.group(1)
            )

    # -----------------------------------------------------
    # UNDEFINED / MISSING INTERFACE
    # -----------------------------------------------------

    if issue_type in {
        "undefined_interface",
        "signal_interface_missing",
    }:

        match = re.search(
            r"\b([A-Za-z][A-Za-z0-9_]*Interface)\b",
            description,
        )

        if match:
            return normalize(
                match.group(1)
            )

    # -----------------------------------------------------
    # UNKNOWN COMPONENT / INVALID DEPENDENCY
    # -----------------------------------------------------

    # These are not present in the current corpus.
    # If future ground truth adds them, the evaluator
    # should preferably use an explicit entity field.

    explicit_entity = issue.get(
        "entity",
        "",
    )

    if explicit_entity:
        return normalize(
            explicit_entity
        )

    return ""


# =========================================================
# EXPECTED STRUCTURAL ISSUES
# =========================================================

def expected_validation_issues(
    document_data,
):
    """
    Return only structural issues that belong to the
    single-document ConsistencyChecker.

    Revision-specific issues such as signal renames
    are evaluated separately by RevisionComparator.
    """

    structural_issue_types = {
        "missing_provider_port",
        "missing_consumer_port",
        "undefined_interface",
        "unknown_component",
        "signal_interface_missing",
        "invalid_dependency",
    }

    expected = set()

    for issue in document_data.get(
        "known_issues",
        [],
    ):

        issue_type = normalize(
            issue.get(
                "type",
                "",
            )
        )

        if (
            issue_type
            not in structural_issue_types
        ):
            continue

        entity = extract_issue_entity(
            issue
        )

        if not entity:
            raise ValueError(
                "Could not determine affected "
                "entity for ground-truth issue "
                f"{issue.get('issue_id', 'UNKNOWN')}: "
                f"{issue.get('description', '')}"
            )

        expected.add(
            (
                issue_type,
                entity,
            )
        )

    return expected


# =========================================================
# DETECTED ISSUES
# =========================================================

def predicted_validation_issues(
    issues,
):

    return {
        (
            normalize(
                issue.issue_type
            ),
            normalize(
                issue.entity
            ),
        )
        for issue in issues
    }


# =========================================================
# METRICS
# =========================================================

def calculate_counts(
    predicted,
    expected,
):

    true_positives = (
        predicted & expected
    )

    false_positives = (
        predicted - expected
    )

    false_negatives = (
        expected - predicted
    )

    return (
        true_positives,
        false_positives,
        false_negatives,
    )


def calculate_metrics(
    tp,
    fp,
    fn,
):

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

    return (
        precision,
        recall,
        f1,
    )


# =========================================================
# MAIN
# =========================================================

def main():

    print("=" * 76)

    print(
        "AUTOSAR HLD ASSISTANT - "
        "CONSISTENCY VALIDATION EVALUATION"
    )

    print("=" * 76)

    with open(
        GROUND_TRUTH_PATH,
        "r",
        encoding="utf-8",
    ) as file:

        dataset = json.load(
            file
        )

    documents = dataset.get(
        "documents",
        {},
    )

    if not documents:

        raise RuntimeError(
            "Ground-truth dataset contains "
            "no documents."
        )

    extractor = (
        PDFArchitectureExtractor()
    )

    checker = (
        ConsistencyChecker()
    )

    total_tp = 0
    total_fp = 0
    total_fn = 0

    evaluated_documents = 0

    # -----------------------------------------------------
    # DOCUMENT-BY-DOCUMENT EVALUATION
    # -----------------------------------------------------

    for (
        filename,
        expected_data,
    ) in documents.items():

        pdf_path = (
            HLD_DIRECTORY
            / filename
        )

        print(
            "\n"
            + "-" * 76
        )

        print(
            f"DOCUMENT: {filename}"
        )

        print(
            "-" * 76
        )

        if not pdf_path.exists():

            print(
                "SKIPPED: PDF not found."
            )

            continue

        architecture = (
            extractor.extract(
                pdf_path
            )
        )

        detected_issues = (
            checker.validate(
                architecture
            )
        )

        predicted = (
            predicted_validation_issues(
                detected_issues
            )
        )

        expected = (
            expected_validation_issues(
                expected_data
            )
        )

        (
            true_positives,
            false_positives,
            false_negatives,
        ) = calculate_counts(
            predicted,
            expected,
        )

        tp = len(
            true_positives
        )

        fp = len(
            false_positives
        )

        fn = len(
            false_negatives
        )

        total_tp += tp
        total_fp += fp
        total_fn += fn

        evaluated_documents += 1

        # -------------------------------------------------
        # EXPECTED
        # -------------------------------------------------

        print(
            "Expected structural issues:"
        )

        if expected:

            for (
                issue_type,
                entity,
            ) in sorted(expected):

                print(
                    f"  {issue_type} | "
                    f"{entity}"
                )

        else:

            print(
                "  None"
            )

        # -------------------------------------------------
        # DETECTED
        # -------------------------------------------------

        print(
            "\nDetected structural issues:"
        )

        if predicted:

            for (
                issue_type,
                entity,
            ) in sorted(predicted):

                print(
                    f"  {issue_type} | "
                    f"{entity}"
                )

        else:

            print(
                "  None"
            )

        # -------------------------------------------------
        # MATCHING DETAILS
        # -------------------------------------------------

        print(
            "\nMatching results:"
        )

        if true_positives:

            for item in sorted(
                true_positives
            ):

                print(
                    "  CORRECT : "
                    f"{item[0]} | "
                    f"{item[1]}"
                )

        if false_positives:

            for item in sorted(
                false_positives
            ):

                print(
                    "  FALSE POSITIVE : "
                    f"{item[0]} | "
                    f"{item[1]}"
                )

        if false_negatives:

            for item in sorted(
                false_negatives
            ):

                print(
                    "  MISSED : "
                    f"{item[0]} | "
                    f"{item[1]}"
                )

        if (
            not true_positives
            and not false_positives
            and not false_negatives
        ):

            print(
                "  No structural issues "
                "expected or detected."
            )

        print(
            f"\nTP={tp}  "
            f"FP={fp}  "
            f"FN={fn}"
        )

    # =====================================================
    # FINAL RESULTS
    # =====================================================

    if evaluated_documents == 0:

        raise RuntimeError(
            "Zero documents were evaluated."
        )

    (
        precision,
        recall,
        f1,
    ) = calculate_metrics(
        total_tp,
        total_fp,
        total_fn,
    )

    print(
        "\n"
        + "=" * 76
    )

    print(
        "AGGREGATE CONSISTENCY "
        "VALIDATION RESULTS"
    )

    print(
        "=" * 76
    )

    print(
        f"Precision : {precision:.3f}"
    )

    print(
        f"Recall    : {recall:.3f}"
    )

    print(
        f"F1        : {f1:.3f}"
    )

    print(
        f"TP={total_tp}  "
        f"FP={total_fp}  "
        f"FN={total_fn}"
    )

    print(
        f"Documents evaluated: "
        f"{evaluated_documents}"
    )

    print(
        "\nImportant:"
    )

    print(
        "These metrics evaluate only the "
        "structural issue types represented "
        "in the current controlled corpus."
    )

    print(
        "Revision-specific issues such as "
        "WheelSpeed -> Wheel_Speed are "
        "evaluated separately by the "
        "RevisionComparator."
    )

    print(
        "\nCONSISTENCY VALIDATION "
        "EVALUATION COMPLETE"
    )


if __name__ == "__main__":
    main()