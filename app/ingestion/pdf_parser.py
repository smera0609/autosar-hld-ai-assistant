from pathlib import Path
import io

import pymupdf
import pytesseract
from PIL import Image

from app.models.document import DocumentData, PageContent


class PDFParser:
    """
    Hybrid PDF parser.

    1. Uses PyMuPDF native text extraction first.
    2. If a page contains insufficient extractable text,
       automatically falls back to Tesseract OCR.
    """

    # If native extraction produces fewer characters than this,
    # the page is treated as potentially scanned/image-based.
    OCR_TEXT_THRESHOLD = 30

    def __init__(
        self,
        tesseract_cmd: str | None = None,
        ocr_dpi: int = 300,
    ):
        self.ocr_dpi = ocr_dpi

        # Explicit path is useful on Windows when Tesseract is
        # installed but is not globally available through PATH.
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

        else:
            default_windows_path = Path(
                r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            )

            if default_windows_path.exists():
                pytesseract.pytesseract.tesseract_cmd = str(
                    default_windows_path
                )

    def parse(self, file_path: str) -> DocumentData:
        pdf_path = Path(file_path)

        if not pdf_path.exists():
            raise FileNotFoundError(
                f"PDF not found: {pdf_path}"
            )

        if pdf_path.suffix.lower() != ".pdf":
            raise ValueError(
                "Only PDF files are supported."
            )

        try:
            document = pymupdf.open(pdf_path)

        except Exception as exc:
            raise ValueError(
                f"Unable to open PDF: {exc}"
            ) from exc

        pages: list[PageContent] = []
        full_text_parts: list[str] = []

        native_pages = 0
        ocr_pages = 0
        empty_pages = 0

        try:

            for index in range(document.page_count):

                page = document.load_page(index)

                # =========================================
                # STEP 1: NORMAL TEXT EXTRACTION
                # =========================================

                native_text = page.get_text("text")

                native_text = self._clean_text(
                    native_text
                )

                text = native_text
                extraction_type = "pymupdf"

                # =========================================
                # STEP 2: OCR FALLBACK
                # =========================================

                if self._needs_ocr(native_text):

                    try:

                        ocr_text = self._ocr_page(
                            page
                        )

                        ocr_text = self._clean_text(
                            ocr_text
                        )

                        # Only replace native text if OCR
                        # actually produced useful content.
                        if len(ocr_text) > len(native_text):

                            text = ocr_text
                            extraction_type = "ocr"

                            ocr_pages += 1

                        elif native_text:

                            native_pages += 1

                        else:

                            empty_pages += 1

                    except Exception:

                        # OCR failure should not destroy
                        # ingestion of the entire document.
                        text = native_text

                        if native_text:
                            native_pages += 1
                        else:
                            empty_pages += 1

                else:

                    native_pages += 1

                # =========================================
                # STORE PAGE
                # =========================================

                pages.append(
                    PageContent(
                        page_number=index + 1,
                        text=text,
                        character_count=len(text),
                    )
                )

                if text:

                    full_text_parts.append(
                        f"[PAGE {index + 1}]\n{text}"
                    )

            # =============================================
            # PDF METADATA
            # =============================================

            metadata = {
                key: value
                for key, value
                in (document.metadata or {}).items()
                if value
            }

            # Add our extraction information.
            metadata["native_text_pages"] = (
                native_pages
            )

            metadata["ocr_pages"] = (
                ocr_pages
            )

            metadata["empty_pages"] = (
                empty_pages
            )

            # =============================================
            # DOCUMENT EXTRACTION METHOD
            # =============================================

            if ocr_pages > 0 and native_pages > 0:

                extraction_method = (
                    "pymupdf+tesseract"
                )

            elif ocr_pages > 0:

                extraction_method = (
                    "tesseract-ocr"
                )

            else:

                extraction_method = (
                    "pymupdf"
                )

            return DocumentData(
                filename=pdf_path.name,
                file_path=str(pdf_path),
                page_count=document.page_count,
                metadata=metadata,
                pages=pages,
                full_text="\n\n".join(
                    full_text_parts
                ),
                extraction_method=extraction_method,
            )

        finally:

            document.close()

    # =====================================================
    # OCR DECISION
    # =====================================================

    def _needs_ocr(
        self,
        text: str,
    ) -> bool:
        """
        Determine whether native PDF text extraction
        produced enough usable content.
        """

        if not text:
            return True

        useful_characters = sum(
            character.isalnum()
            for character in text
        )

        return (
            useful_characters
            < self.OCR_TEXT_THRESHOLD
        )

    # =====================================================
    # OCR PAGE
    # =====================================================

    def _ocr_page(
        self,
        page,
    ) -> str:
        """
        Render a PDF page as a high-resolution image
        and run Tesseract OCR on it.
        """

        zoom = self.ocr_dpi / 72

        matrix = pymupdf.Matrix(
            zoom,
            zoom,
        )

        pixmap = page.get_pixmap(
            matrix=matrix,
            alpha=False,
        )

        image_bytes = pixmap.tobytes(
            "png"
        )

        image = Image.open(
            io.BytesIO(image_bytes)
        )

        try:

            text = pytesseract.image_to_string(
                image,
                lang="eng",
                config="--psm 6",
            )

        finally:

            image.close()

        return text

    # =====================================================
    # TEXT CLEANING
    # =====================================================

    @staticmethod
    def _clean_text(
        text: str,
    ) -> str:

        lines = []

        for line in text.splitlines():

            cleaned = " ".join(
                line.split()
            )

            if cleaned:
                lines.append(cleaned)

        return "\n".join(lines)