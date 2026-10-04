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


class PDFArchitectureExtractor:
    """
    Extract structured architecture entities directly from HLD PDF tables.

    Ground-truth data is NOT used by this class.
    """

    def extract(
        self,
        file_path: str,
    ) -> ArchitectureModel:

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

        with pdfplumber.open(path) as pdf:

            # Metadata is extracted from the visible
            # document-control table.
            for page in pdf.pages:

                tables = page.extract_tables()

                for table in tables:

                    if not table or len(table) < 2:
                        continue

                    cleaned = self._clean_table(table)

                    if not cleaned:
                        continue

                    headers = [
                        self._normalise(cell)
                        for cell in cleaned[0]
                    ]

                    # -------------------------
                    # DOCUMENT CONTROL TABLE
                    # -------------------------

                    if (
                        "field" in headers
                        and "value" in headers
                    ):

                        for row in cleaned[1:]:

                            if len(row) < 2:
                                continue

                            field = self._clean(row[0])
                            value = self._clean(row[1])

                            if (
                                field.lower()
                                == "document id"
                            ):
                                document_id = value

                            elif (
                                field.lower()
                                == "version"
                            ):
                                version = value

                    # -------------------------
                    # COMPONENT TABLE
                    # -------------------------

                    elif (
                        "component" in headers
                        and "responsibility" in headers
                    ):

                        for row in cleaned[1:]:

                            if len(row) < 2:
                                continue

                            name = self._clean(row[0])
                            description = self._clean(
                                row[1]
                            )

                            if name:
                                components.append(
                                    Component(
                                        name=name,
                                        description=description,
                                    )
                                )

                    # -------------------------
                    # INTERFACE TABLE
                    # -------------------------

                    elif (
                        "interface" in headers
                        and "provider" in headers
                        and "consumer" in headers
                        and "port" not in headers
                    ):

                        for row in cleaned[1:]:

                            if len(row) < 3:
                                continue

                            name = self._clean(row[0])

                            if name:
                                interfaces.append(
                                    Interface(
                                        name=name,
                                        provider=self._clean(
                                            row[1]
                                        ),
                                        consumer=self._clean(
                                            row[2]
                                        ),
                                    )
                                )

                    # -------------------------
                    # PORT TABLE
                    # -------------------------

                    elif (
                        "component" in headers
                        and "port" in headers
                        and "port type" in headers
                        and "interface" in headers
                    ):

                        for row in cleaned[1:]:

                            if len(row) < 4:
                                continue

                            if not self._clean(row[1]):
                                continue

                            ports.append(
                                Port(
                                    component=self._clean(
                                        row[0]
                                    ),
                                    name=self._clean(
                                        row[1]
                                    ),
                                    port_type=self._clean(
                                        row[2]
                                    ),
                                    interface=self._clean(
                                        row[3]
                                    ),
                                )
                            )

                    # -------------------------
                    # SIGNAL TABLE
                    # -------------------------

                    elif (
                        "signal" in headers
                        and "interface" in headers
                        and "unit" in headers
                    ):

                        for row in cleaned[1:]:

                            if len(row) < 3:
                                continue

                            name = self._clean(row[0])

                            if name:
                                signals.append(
                                    Signal(
                                        name=name,
                                        interface=self._clean(
                                            row[1]
                                        ),
                                        unit=self._clean(
                                            row[2]
                                        ),
                                    )
                                )

                    # -------------------------
                    # DEPENDENCY TABLE
                    # -------------------------

                    elif (
                        "dependent component"
                        in headers
                        and "required component"
                        in headers
                    ):

                        for row in cleaned[1:]:

                            if len(row) < 2:
                                continue

                            dependent = self._clean(
                                row[0]
                            )

                            required = self._clean(
                                row[1]
                            )

                            if dependent and required:

                                dependencies.append(
                                    Dependency(
                                        dependent_component=(
                                            dependent
                                        ),
                                        required_component=(
                                            required
                                        ),
                                    )
                                )

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

        value = self._clean(value)

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value.lower()

    def _clean_table(
        self,
        table,
    ):

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