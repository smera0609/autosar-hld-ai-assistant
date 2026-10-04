from app.database.review_store import (
    ReviewStore,
)


def main():

    print("=" * 70)
    print("SQLITE ENGINEER REVIEW TEST")
    print("=" * 70)

    store = ReviewStore(
        "data/test_reviews.db"
    )

    document_name = (
        "Vehicle_Control_HLD_v2.pdf"
    )

    # Clean previous test data so repeated
    # test runs give predictable results.
    store.delete_document_reviews(
        document_name
    )

    # --------------------------------------------------
    # SAVE FIRST REVIEW
    # --------------------------------------------------

    store.save_review(
        document_name=document_name,
        finding_id="REV-001",
        finding_type="SIGNAL RENAMED",
        source="Revision Comparison",
        description=(
            "WheelSpeed renamed to "
            "Wheel_Speed."
        ),
        decision="Accepted",
        comment=(
            "Verified against the newer "
            "HLD revision."
        ),
    )

    # --------------------------------------------------
    # SAVE SECOND REVIEW
    # --------------------------------------------------

    store.save_review(
        document_name=document_name,
        finding_id="VAL-001",
        finding_type="MISSING_PROVIDER_PORT",
        source="Consistency Validation",
        description=(
            "DiagnosticStatusInterface "
            "has no provider P-Port."
        ),
        decision="Pending",
        comment="Requires architect review.",
    )

    # --------------------------------------------------
    # READ REVIEWS
    # --------------------------------------------------

    reviews = store.get_reviews(
        document_name
    )

    print("\nStored Reviews:")

    for review in reviews:

        print(
            review["finding_id"],
            "|",
            review["decision"],
            "|",
            review["comment"],
        )

    # --------------------------------------------------
    # TEST UPDATE / UPSERT
    # --------------------------------------------------

    store.save_review(
        document_name=document_name,
        finding_id="VAL-001",
        finding_type="MISSING_PROVIDER_PORT",
        source="Consistency Validation",
        description=(
            "DiagnosticStatusInterface "
            "has no provider P-Port."
        ),
        decision="Rejected",
        comment=(
            "Reviewed by engineer and "
            "rejected as intentional."
        ),
    )

    updated = store.get_review(
        document_name,
        "VAL-001",
    )

    print("\nUpdated Review:")

    print(
        updated["finding_id"],
        "|",
        updated["decision"],
        "|",
        updated["comment"],
    )

    # --------------------------------------------------
    # SUMMARY
    # --------------------------------------------------

    summary = store.get_review_summary(
        document_name
    )

    print("\nReview Summary:")
    print(summary)

    # --------------------------------------------------
    # ASSERTIONS
    # --------------------------------------------------

    assert len(
        store.get_reviews(
            document_name
        )
    ) == 2

    assert (
        updated["decision"]
        == "Rejected"
    )

    assert (
        summary["Accepted"]
        == 1
    )

    assert (
        summary["Rejected"]
        == 1
    )

    assert (
        summary["Pending"]
        == 0
    )

    print(
        "\nSQLITE REVIEW STORE TEST PASSED"
    )


if __name__ == "__main__":
    main()