"""
Document OCR Engine for Indian KYC and Vehicle Regulatory Documents.

Supports validation, classification, and structured extraction for:
- Aadhaar Card (`aadhaar`)
- Driving License (`driving_license`)
- Registration Certificate (`registration_certificate`)
- Pollution Under Control Certificate (`puc`)
- Vehicle Insurance (`insurance`)
"""

from typing import Any

from .classifier import classify
from .engine import extract_text
from .exceptions import InvalidDocumentError, OCRExtractionError
from .parsers import PARSER_REGISTRY
from .sanitizer import clean_text, mask_tail, sanitize_result
from .schema import (
    AadhaarData,
    DocumentData,
    DrivingLicenseData,
    InsuranceData,
    OCRResult,
    PUCCertificateData,
    RegistrationCertificateData,
)
from .validators import numeric_value, validate_pdf


def process_document(
    pdf_bytes: bytes,
    doc_type: str | None = None,
    mask_pii: bool = False,
) -> dict[str, Any]:
    """
    Process an uploaded document PDF, auto-classifying (or using provided doc_type),
    running OCR extraction, and returning sanitized structured metadata.

    Args:
        pdf_bytes (bytes): Binary PDF content.
        doc_type (str, optional): Target document type if known. Defaults to auto-classification.
        mask_pii (bool): Optional flag to mask sensitive identifier numbers. Defaults to False.

    Returns:
        dict[str, Any]: Standardized extraction output with 'document_type', 'confidence', 'data'.
    """
    validate_pdf(pdf_bytes)
    raw_text = clean_text(extract_text(pdf_bytes))
    if not raw_text:
        return sanitize_result(
            {
                "status": "error",
                "error_code": "no_text",
                "document_type": doc_type or "unknown",
            }
        )

    document_type = doc_type or classify(raw_text)
    parser_cls = PARSER_REGISTRY.get(document_type)
    if not parser_cls:
        return sanitize_result(
            {
                "status": "error",
                "error_code": "unknown_document_type",
                "document_type": document_type,
            }
        )

    parser = parser_cls()
    parsed_data = parser.parse(raw_text, mask=mask_pii)
    filled_fields = sum(
        val not in (None, "", [], False) for val in parsed_data.values()
    )
    confidence = round(filled_fields / len(parsed_data), 2) if parsed_data else 0.0

    return sanitize_result(
        {
            "status": "ok",
            "document_type": document_type,
            "confidence": confidence,
            "data": parsed_data,
        }
    )


__all__ = [
    "AadhaarData",
    "DocumentData",
    "DrivingLicenseData",
    "InsuranceData",
    "InvalidDocumentError",
    "OCRExtractionError",
    "OCRResult",
    "PUCCertificateData",
    "RegistrationCertificateData",
    "classify",
    "extract_text",
    "mask_tail",
    "numeric_value",
    "process_document",
    "sanitize_result",
    "validate_pdf",
]
