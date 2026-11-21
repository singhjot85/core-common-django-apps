"""
Low-level text extraction engine utilizing PyMuPDF and Tesseract OCR.
"""

import io
import logging

from .exceptions import InvalidDocumentError, OCRExtractionError
from .validators import validate_pdf

LOGGER = logging.getLogger(__name__)


def extract_text(
    pdf_bytes: bytes,
    dpi: int = 300,
    lang: str = "eng+hin",
    min_chars: int | None = None,
) -> str:
    """
    Extract text content from a PDF document.

    First attempts fast direct text extraction; if insufficient text is found
    (scanned raster image), renders the page to image and runs Tesseract OCR.

    Args:
        pdf_bytes (bytes): Binary PDF content.
        dpi (int): Resolution to render PDF pages when running optical character recognition.
        lang (str): Tesseract language codes separated by '+'.
        min_chars (int, optional): Minimum characters in direct text to skip OCR. Defaults to CRM app_settings.

    Returns:
        str: Consolidated extracted text across all document pages.

    Raises:
        InvalidDocumentError: If PDF format constraints are violated.
        OCRExtractionError: If extraction dependencies fail during execution.
    """
    validate_pdf(pdf_bytes)

    if min_chars is None:
        try:
            from core.apps.crm import app_settings  # noqa: PLC0415

            min_chars = app_settings.ocr_native_text_min_chars
        except Exception:
            min_chars = 50

    try:
        import pymupdf  # noqa: PLC0415
    except ImportError as exc:
        LOGGER.warning("pymupdf is not installed. OCR extraction cannot proceed.")
        raise OCRExtractionError(
            "pymupdf library is required for PDF parsing."
        ) from exc

    try:
        import pytesseract  # noqa: PLC0415
        from PIL import Image  # noqa: PLC0415
    except ImportError as exc:
        LOGGER.warning(
            "pytesseract or Pillow is not installed (%s). Falling back to direct PDF text extraction only.",
            exc,
        )
        Image = None
        pytesseract = None

    try:
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise InvalidDocumentError("Could not open PDF file stream.") from exc

    texts: list[str] = []
    zoom = dpi / 72.0
    mat = pymupdf.Matrix(zoom, zoom)

    try:
        for page in doc:
            direct_text = page.get_text().strip()
            # If native text layer contains sufficient characters, prefer it over OCR
            if len(direct_text) >= min_chars:
                LOGGER.debug(
                    "Native text layer on page %s has %d chars (threshold: %d); using direct text.",
                    page.number,
                    len(direct_text),
                    min_chars,
                )
                texts.append(direct_text)
                continue

            # Scanned page fallback to Tesseract OCR
            if pytesseract and Image:
                try:
                    pix = page.get_pixmap(matrix=mat, alpha=False)
                    image = Image.open(io.BytesIO(pix.tobytes("png")))
                    ocr_text = pytesseract.image_to_string(image, lang=lang)
                    texts.append(ocr_text.strip())
                except Exception as exc:
                    LOGGER.warning(
                        "Tesseract OCR failed on page %s: %s", page.number, exc
                    )
                    if direct_text:
                        texts.append(direct_text)
            elif direct_text:
                LOGGER.info(
                    "OCR dependencies unavailable on page %s; using native text layer fallback (%d chars).",
                    page.number,
                    len(direct_text),
                )
                texts.append(direct_text)
            else:
                LOGGER.warning(
                    "Page %s has insufficient native text and OCR engine is unavailable.",
                    page.number,
                )
    finally:
        doc.close()

    return "\n".join(t for t in texts if t)
