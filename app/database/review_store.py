import sqlite3
from datetime import datetime
from pathlib import Path


class ReviewStore:
    """
    Persistent SQLite storage for engineer review decisions.

    Each review records:
    - document
    - finding
    - finding type
    - source
    - engineer decision
    - engineer comment
    - timestamp
    """

    def __init__(
        self,
        db_path: str = "data/reviews.db",
    ):
        self.db_path = Path(db_path)

        # Make sure the parent directory exists.
        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._create_table()

    # -----------------------------------------------------
    # DATABASE CONNECTION
    # -----------------------------------------------------

    def _connect(self):
        return sqlite3.connect(
            self.db_path
        )

    # -----------------------------------------------------
    # CREATE TABLE
    # -----------------------------------------------------

    def _create_table(self):
        with self._connect() as connection:

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS engineer_reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    document_name TEXT NOT NULL,

                    finding_id TEXT NOT NULL,

                    finding_type TEXT NOT NULL,

                    source TEXT NOT NULL,

                    description TEXT NOT NULL,

                    decision TEXT NOT NULL,

                    comment TEXT DEFAULT '',

                    reviewed_at TEXT NOT NULL,

                    UNIQUE(
                        document_name,
                        finding_id
                    )
                )
                """
            )

            connection.commit()

    # -----------------------------------------------------
    # SAVE / UPDATE REVIEW
    # -----------------------------------------------------

    def save_review(
        self,
        document_name: str,
        finding_id: str,
        finding_type: str,
        source: str,
        description: str,
        decision: str,
        comment: str = "",
    ):
        """
        Save a new engineer review.

        If the same finding has already been reviewed,
        update the existing review instead of creating
        a duplicate row.
        """

        allowed_decisions = {
            "Pending",
            "Accepted",
            "Rejected",
        }

        if decision not in allowed_decisions:
            raise ValueError(
                f"Invalid review decision: {decision}"
            )

        reviewed_at = (
            datetime.now()
            .astimezone()
            .isoformat(
                timespec="seconds"
            )
        )

        with self._connect() as connection:

            connection.execute(
                """
                INSERT INTO engineer_reviews (
                    document_name,
                    finding_id,
                    finding_type,
                    source,
                    description,
                    decision,
                    comment,
                    reviewed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)

                ON CONFLICT(
                    document_name,
                    finding_id
                )
                DO UPDATE SET

                    finding_type =
                        excluded.finding_type,

                    source =
                        excluded.source,

                    description =
                        excluded.description,

                    decision =
                        excluded.decision,

                    comment =
                        excluded.comment,

                    reviewed_at =
                        excluded.reviewed_at
                """,
                (
                    document_name,
                    finding_id,
                    finding_type,
                    source,
                    description,
                    decision,
                    comment,
                    reviewed_at,
                ),
            )

            connection.commit()

    # -----------------------------------------------------
    # GET REVIEWS FOR ONE DOCUMENT
    # -----------------------------------------------------

    def get_reviews(
        self,
        document_name: str,
    ):
        with self._connect() as connection:

            connection.row_factory = (
                sqlite3.Row
            )

            rows = connection.execute(
                """
                SELECT
                    id,
                    document_name,
                    finding_id,
                    finding_type,
                    source,
                    description,
                    decision,
                    comment,
                    reviewed_at

                FROM engineer_reviews

                WHERE document_name = ?

                ORDER BY id ASC
                """,
                (
                    document_name,
                ),
            ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    # -----------------------------------------------------
    # GET ONE REVIEW
    # -----------------------------------------------------

    def get_review(
        self,
        document_name: str,
        finding_id: str,
    ):
        with self._connect() as connection:

            connection.row_factory = (
                sqlite3.Row
            )

            row = connection.execute(
                """
                SELECT
                    id,
                    document_name,
                    finding_id,
                    finding_type,
                    source,
                    description,
                    decision,
                    comment,
                    reviewed_at

                FROM engineer_reviews

                WHERE
                    document_name = ?
                    AND finding_id = ?
                """,
                (
                    document_name,
                    finding_id,
                ),
            ).fetchone()

        if row is None:
            return None

        return dict(row)

    # -----------------------------------------------------
    # REVIEW COUNTS
    # -----------------------------------------------------

    def get_review_summary(
        self,
        document_name: str,
    ):
        summary = {
            "Pending": 0,
            "Accepted": 0,
            "Rejected": 0,
        }

        with self._connect() as connection:

            rows = connection.execute(
                """
                SELECT
                    decision,
                    COUNT(*) AS total

                FROM engineer_reviews

                WHERE document_name = ?

                GROUP BY decision
                """,
                (
                    document_name,
                ),
            ).fetchall()

        for decision, total in rows:

            if decision in summary:
                summary[decision] = total

        return summary

    # -----------------------------------------------------
    # DELETE REVIEWS FOR DOCUMENT
    # -----------------------------------------------------

    def delete_document_reviews(
        self,
        document_name: str,
    ):
        with self._connect() as connection:

            connection.execute(
                """
                DELETE FROM engineer_reviews
                WHERE document_name = ?
                """,
                (
                    document_name,
                ),
            )

            connection.commit()