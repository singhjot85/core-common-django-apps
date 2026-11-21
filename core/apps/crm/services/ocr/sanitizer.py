"""
Sanitization, PII masking, and string cleaning utilities for Document OCR.
"""

import re
from typing import Any

from .schema import OCRResult


def clean_text(text: str) -> str:
    """
    Normalize whitespace characters across a text string.

    Args:
        text (str): Input raw text.

    Returns:
        str: Collapsed single-space string.
    """
    return " ".join(text.split())


def after_label(text: str, labels: list[str]) -> str | None:
    """
    Extract text appearing immediately after one of the specified label patterns.

    Args:
        text (str): Document text block.
        labels (list[str]): List of regex label markers.

    Returns:
        str | None: Extracted string following the label or None.
    """
    for label in labels:
        match = re.search(rf"{label}\s*[:\-]?\s*([^\n\r]+)", text, re.I)
        if match:
            return match.group(1).strip()
    return None


def clean_name(value: str | None) -> str | None:
    """
    Clean extracted candidate person names by removing leading label prefixes and non-alpha noise.

    Args:
        value (str | None): Raw name candidate.

    Returns:
        str | None: Cleaned person name or None if invalid.
    """
    if not value:
        return None
    cleaned = re.sub(
        r"^(?:Name|Father'?s Name|Husband'?s Name|Guardian'?s Name)\s*[:\-]?\s*",
        "",
        value,
        flags=re.I,
    )
    cleaned = re.sub(r"[^A-Za-z\s.]", "", cleaned)
    cleaned = " ".join(cleaned.split())
    return cleaned if len(cleaned) > 2 else None


def mask_tail(value: str | None, keep: int = 4) -> str | None:
    """
    Mask all leading characters of a sensitive identifier, keeping only the final digits.

    Args:
        value (str | None): Sensitive identifier string.
        keep (int): Number of trailing characters to retain in plaintext.

    Returns:
        str | None: Masked string (e.g., 'XXXXXXXX1234') or None.
    """
    if not value:
        return None
    val = value.strip()
    if len(val) <= keep:
        return val
    return "X" * (len(val) - keep) + val[-keep:]


def sanitize_result(result: dict[str, Any] | OCRResult) -> dict[str, Any]:
    """
    Sanitize and enforce structural contract on raw OCR extraction output using OCRResult dataclass.

    Args:
        result (dict[str, Any] | OCRResult): Raw or parsed OCR output.

    Returns:
        dict[str, Any]: Structured dictionary conforming to API contract.
    """
    if isinstance(result, OCRResult):
        return result.to_dict()

    if "error_code" in result or result.get("status") == "error":
        return OCRResult(
            status="error",
            document_type=result.get("document_type", "unknown"),
            confidence=0.0,
            error_code=result.get("error_code", "unknown_error"),
            data={},
        ).to_dict()

    raw_data = result.get("data", {})
    sanitized_data: dict[str, Any] = {}

    for key, value in raw_data.items():
        if value is None or value == "":
            continue
        if isinstance(value, str):
            cleaned = value.strip()
            if cleaned:
                sanitized_data[key] = cleaned
        elif isinstance(value, list):
            cleaned_list = [
                v.strip() if isinstance(v, str) else v
                for v in value
                if v not in (None, "")
            ]
            if cleaned_list:
                sanitized_data[key] = cleaned_list
        elif isinstance(value, (int, float, bool)):
            sanitized_data[key] = value
        elif isinstance(value, dict):
            sanitized_data[key] = {
                k: v.strip() if isinstance(v, str) else v
                for k, v in value.items()
                if v not in (None, "")
            }

    confidence = float(result.get("confidence", 0.0))
    doc_type = result.get("document_type", "unknown")

    return OCRResult(
        status="ok",
        document_type=doc_type,
        confidence=confidence,
        data=sanitized_data,
    ).to_dict()
