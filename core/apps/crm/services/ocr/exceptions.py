"""
Custom exception types for the Document OCR engine.
"""


class InvalidDocumentError(ValueError):
    """
    Raised when an uploaded document file is invalid, corrupt, encrypted,
    exceeds size/page limits, or is unsupported.
    """


class OCRExtractionError(RuntimeError):
    """
    Raised when the text extraction engine encounters an unrecoverable error.
    """
