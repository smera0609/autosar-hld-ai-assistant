from app.ingestion.pdf_parser import PDFParser
from app.ingestion.chunker import DocumentChunker


class DocumentProcessor:
    def __init__(
        self,
        chunk_size: int = 1200,
        chunk_overlap: int = 200,
    ):
        self.parser = PDFParser()

        self.chunker = DocumentChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def process(self, file_path: str):

        document = self.parser.parse(file_path)

        chunks = self.chunker.chunk_document(document)

        return {
            "document": document,
            "chunks": chunks,
        }