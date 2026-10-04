from app.models.document import DocumentChunk, DocumentData


class DocumentChunker:
    """
    Splits HLD pages into overlapping, retrieval-friendly chunks while
    preserving document and page provenance.
    """

    def __init__(
        self,
        chunk_size: int = 1200,
        chunk_overlap: int = 200,
    ):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0.")

        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative.")

        if chunk_overlap >= chunk_size:
            raise ValueError(
                "chunk_overlap must be smaller than chunk_size."
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(
        self,
        document: DocumentData,
    ) -> list[DocumentChunk]:

        chunks = []

        for page in document.pages:

            text = page.text.strip()

            if not text:
                continue

            page_chunks = self._create_chunks(text)

            for index, (chunk_text, start, end) in enumerate(
                page_chunks,
                start=1,
            ):

                chunks.append(
                    DocumentChunk(
                        chunk_id=(
                            f"{document.filename}"
                            f"_p{page.page_number}"
                            f"_c{index}"
                        ),
                        filename=document.filename,
                        page_number=page.page_number,
                        section=None,
                        text=chunk_text,
                        start_char=start,
                        end_char=end,
                    )
                )

        return chunks

    def _create_chunks(
        self,
        text: str,
    ) -> list[tuple[str, int, int]]:

        chunks = []

        start = 0
        length = len(text)

        while start < length:

            target_end = min(
                start + self.chunk_size,
                length,
            )

            end = target_end

            if target_end < length:

                candidates = [
                    text.rfind("\n\n", start, target_end),
                    text.rfind("\n", start, target_end),
                    text.rfind(". ", start, target_end),
                ]

                best_break = max(candidates)

                minimum_break = (
                    start + int(self.chunk_size * 0.6)
                )

                if best_break >= minimum_break:
                    end = best_break + 1

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append(
                    (
                        chunk_text,
                        start,
                        end,
                    )
                )

            if end >= length:
                break

            next_start = end - self.chunk_overlap

            if next_start <= start:
                next_start = end

            start = next_start

        return chunks