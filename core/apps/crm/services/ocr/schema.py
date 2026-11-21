"""
Data structures and dataclasses for Document OCR extraction.
"""

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class DocumentData:
    """Base dataclass for parsed document metadata."""

    def to_dict(self) -> dict[str, Any]:
        """
        Convert dataclass fields to dictionary, omitting None values and empty sequences.

        Returns:
            dict[str, Any]: Clean dictionary representation.
        """
        return {
            k: v
            for k, v in asdict(self).items()
            if v is not None and v != "" and v != []
        }


@dataclass
class AadhaarData(DocumentData):
    """Extracted fields for Indian UIDAI Aadhaar cards."""

    aadhaar_number: str | None = None
    name: str | None = None
    gender: str | None = None
    dob: str | None = None
    year_of_birth: int | None = None


@dataclass
class DrivingLicenseData(DocumentData):
    """Extracted fields for Indian State Driving Licenses."""

    license_number: str | None = None
    name: str | None = None
    guardian_name: str | None = None
    dob: str | None = None
    date_of_issue: str | None = None
    valid_upto_non_transport: str | None = None
    valid_upto_transport: str | None = None
    blood_group: str | None = None
    vehicle_classes: list[str] = field(default_factory=list)
    address: str | None = None
    pin_code: str | None = None
    state_code: str | None = None


@dataclass
class RegistrationCertificateData(DocumentData):
    """Extracted fields for Vehicle Registration Certificates (RC)."""

    registration_no: str | None = None
    chassis_no: str | None = None
    engine_no: str | None = None
    owner_name: str | None = None
    vehicle_class: str | None = None
    reg_date: str | None = None
    fitness_upto: str | None = None


@dataclass
class PUCCertificateData(DocumentData):
    """Extracted fields for Pollution Under Control (PUC) Certificates."""

    vehicle_number: str | None = None
    certificate_number: str | None = None
    test_date: str | None = None
    valid_upto: str | None = None
    fuel_type: str | None = None


@dataclass
class InsuranceData(DocumentData):
    """Extracted fields for Vehicle Insurance Policies."""

    policy_number: str | None = None
    vehicle_number: str | None = None
    insurer: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    idv: float | None = None
    total_premium: float | None = None


@dataclass
class OCRResult:
    """Standardized response output for OCR processing pipeline."""

    document_type: str = "unknown"
    confidence: float = 0.0
    data: dict[str, Any] = field(default_factory=dict)
    error_code: str | None = None
    status: str = "ok"

    def to_dict(self) -> dict[str, Any]:
        """
        Convert OCRResult to a clean API dictionary.

        Returns:
            dict[str, Any]: Formatted result dictionary.
        """
        result: dict[str, Any] = {
            "status": self.status,
            "document_type": self.document_type,
            "confidence": self.confidence,
            "data": self.data,
        }
        if self.error_code:
            result["error_code"] = self.error_code
        return result
