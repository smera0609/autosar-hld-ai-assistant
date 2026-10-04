from pathlib import Path
import io

import pymupdf
from PIL import Image


SOURCE_DIR = Path("data/sample_hlds")

PDF_FILES = [
    "Vehicle_Control_HLD_v1.pdf",
    "Vehicle_Control_HLD_v2.pdf",
    "Braking_System_HLD.pdf",
    "Door_Control_HLD.pdf",
    "Body_Control_HLD.pdf",
]


def create_scanned_pdf(
    source_path: Path,
    output_path: Path,
):
    """
    Convert a normal PDF into an image-only scanned PDF.

    Each source page is rendered as an image and then written
    back into a PDF. The resulting PDF has no native text layer,
    forcing our ingestion pipeline to use Tesseract OCR.
    """

    document = pymupdf.open(source_path)

    images = []

    try:
        for page in document:

            # Render at approximately 2x resolution.
            pixmap = page.get_pixmap(
                matrix=pymupdf.Matrix(2, 2),
                alpha=False,
            )

            image_bytes = pixmap.tobytes("png")

            image = Image.open(
                io.BytesIO(image_bytes)
            ).convert("RGB")

            images.append(image.copy())

    finally:
        document.close()

    if not images:
        raise ValueError(
            f"No pages found in {source_path}"
        )

    # Save pages as an image-only PDF.
    first_image = images[0]

    remaining_images = images[1:]

    first_image.save(
        output_path,
        "PDF",
        save_all=True,
        append_images=remaining_images,
        resolution=150.0,
    )

    for image in images:
        image.close()


def main():

    print()
    print("Creating scanned HLD evaluation corpus...")
    print("=" * 60)

    created = 0

    for filename in PDF_FILES:

        source_path = SOURCE_DIR / filename

        if not source_path.exists():

            print(
                f"[SKIP] Source not found: "
                f"{source_path}"
            )

            continue

        stem = source_path.stem

        output_path = (
            SOURCE_DIR
            / f"{stem}_SCANNED.pdf"
        )

        create_scanned_pdf(
            source_path,
            output_path,
        )

        created += 1

        print(
            f"[OK] {filename}"
        )

        print(
            f"     -> {output_path.name}"
        )

    print("=" * 60)

    print(
        f"Created {created} scanned PDF(s)."
    )


if __name__ == "__main__":
    main()