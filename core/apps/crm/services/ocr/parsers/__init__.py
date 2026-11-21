"""
Registry and entry point for Document OCR Parsers.
"""

from typing import Type

from .aadhaar import AadhaarParser
from .base import BaseDocumentParser
from .insurance import InsuranceParser
from .license import DrivingLicenseParser
from .puc import PUCCertificateParser
from .rc import RegistrationCertificateParser

PARSER_REGISTRY: dict[str, Type[BaseDocumentParser]] = {
    "aadhaar": AadhaarParser,
    "driving_license": DrivingLicenseParser,
    "puc": PUCCertificateParser,
    "insurance": InsuranceParser,
    "registration_certificate": RegistrationCertificateParser,
}

__all__ = [
    "BaseDocumentParser",
    "AadhaarParser",
    "DrivingLicenseParser",
    "PUCCertificateParser",
    "InsuranceParser",
    "RegistrationCertificateParser",
    "PARSER_REGISTRY",
]
