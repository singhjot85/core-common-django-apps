"""
Validation and normalization helpers for the Document OCR engine.
"""

import re
from datetime import datetime

from .exceptions import InvalidDocumentError

_VERHOEFF_D = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]

_VERHOEFF_P = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]

_VEHICLE_RE = re.compile(
    r"\b([A-Z]{2})[\s-]?(\d{1,2})[\s-]?([A-Z]{1,3})[\s-]?(\d{4})\b"
)
_BH_VEHICLE_RE = re.compile(r"\b(\d{2})\s?BH\s?(\d{4})\s?([A-Z]{1,2})\b")

MAX_DOCUMENT_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_PAGE_COUNT = 10


def verhoeff_ok(number: str) -> bool:
    """
    Validate a numerical string using the Verhoeff checksum algorithm.

    Args:
        number (str): Digits-only string (e.g. 12-digit Aadhaar number).

    Returns:
        bool: True if checksum validates, False otherwise.
    """
    checksum = 0
    for index, character in enumerate(reversed(number)):
        checksum = _VERHOEFF_D[checksum][_VERHOEFF_P[index % 8][int(character)]]
    return checksum == 0


def norm_date(raw: str | None) -> str | None:
    """
    Normalize various date string formats into ISO 8601 (YYYY-MM-DD).

    Args:
        raw (str | None): Input date string.

    Returns:
        str | None: Standardized YYYY-MM-DD date string or None if unparseable.
    """
    if not raw:
        return None
    cleaned = re.sub(r"[^\d/\-.]", "", raw.strip())
    for fmt in (
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d.%m.%Y",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d/%m/%y",
        "%d-%m-%y",
    ):
        try:
            return datetime.strptime(cleaned, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def find_dates(text: str) -> list[str]:
    """
    Locate and normalize all date strings in the given text block.

    Args:
        text (str): Arbitrary text block.

    Returns:
        list[str]: Normalized date strings.
    """
    matches = re.findall(r"\b\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}\b", text)
    results = [norm_date(m) for m in matches]
    return [d for d in results if d]


def find_vehicle_no(text: str) -> str | None:
    """
    Find and format standard Indian or BH-series vehicle registration numbers.

    Args:
        text (str): Arbitrary text block.

    Returns:
        str | None: Formatted registration string (e.g., 'DL 01 AB 1234') or None.
    """
    match = _VEHICLE_RE.search(text)
    if match:
        state, rto, series, num = match.groups()
        return f"{state.upper()}{rto.zfill(2)}{series.upper()}{num}"
    bh = _BH_VEHICLE_RE.search(text)
    if bh:
        year, num, series = bh.groups()
        return f"{year}BH{num}{series.upper()}"
    return None


def validate_pdf(
    pdf_bytes: bytes,
    max_size: int = MAX_DOCUMENT_SIZE,
    max_pages: int = MAX_PAGE_COUNT,
) -> None:
    """
    Validate that bytes represent an unencrypted PDF within size and page limits.

    Args:
        pdf_bytes (bytes): Binary content of the PDF file.
        max_size (int): Maximum allowed file size in bytes.
        max_pages (int): Maximum allowed page count.

    Raises:
        InvalidDocumentError: If PDF structure or constraints are violated.
    """
    if len(pdf_bytes) > max_size:
        raise InvalidDocumentError(
            f"File size exceeds maximum allowed limit of {max_size // (1024 * 1024)} MB."
        )

    if not pdf_bytes.startswith(b"%PDF-"):
        raise InvalidDocumentError("Uploaded file is not a valid PDF.")

    try:
        import pymupdf

        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    except ImportError:
        # Fallback when pymupdf is not installed in the current environment
        return
    except Exception as exc:
        raise InvalidDocumentError("Failed to parse PDF document structure.") from exc

    try:
        if doc.is_encrypted:
            raise InvalidDocumentError("Encrypted or password-protected PDFs are not supported.")

        if doc.page_count < 1 or doc.page_count > max_pages:
            raise InvalidDocumentError(
                f"PDF must have between 1 and {max_pages} pages (received {doc.page_count})."
            )
    finally:
        doc.close()
