"""
Low-level text extraction engine utilizing PyMuPDF and Tesseract OCR.
"""

import io
import logging

from .exceptions import InvalidDocumentError, OCRExtractionError
from .validators import validate_pdf

LOGGER = logging.getLogger(__name__)


def extract_text(pdf_bytes: bytes, dpi: int = 300, lang: str = "eng+hin") -> str:
    """
    Extract text content from a PDF document.

    First attempts fast direct text extraction; if insufficient text is found
    (scanned raster image), renders the page to image and runs Tesseract OCR.

    Args:
        pdf_bytes (bytes): Binary PDF content.
        dpi (int): Resolution to render PDF pages when running optical character recognition.
        lang (str): Tesseract language codes separated by '+'.

    Returns:
        str: Consolidated extracted text across all document pages.

    Raises:
        InvalidDocumentError: If PDF format constraints are violated.
        OCRExtractionError: If extraction dependencies fail during execution.
    """
    validate_pdf(pdf_bytes)

    try:
        import pymupdf
    except ImportError as exc:
        LOGGER.warning("pymupdf is not installed. OCR extraction cannot proceed.")
        raise OCRExtractionError("pymupdf library is required for PDF parsing.") from exc

    try:
        from PIL import Image
        import pytesseract
    except ImportError:
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
            if len(direct_text) >= 50:
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
                    LOGGER.warning("Tesseract OCR failed on page %s: %s", page.number, exc)
                    if direct_text:
                        texts.append(direct_text)
            elif direct_text:
                texts.append(direct_text)
    finally:
        doc.close()

    return "\n".join(t for t in texts if t)
