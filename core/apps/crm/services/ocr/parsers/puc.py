"""
PUC (Pollution Under Control) document parser implementation.
"""

import re
from typing import Any

from ..validators import find_vehicle_no, norm_date
from .base import BaseDocumentParser


class PUCCertificateParser(BaseDocumentParser):
    """
    Parser for Indian Pollution Under Control (PUC) certificates.
    """

    doc_type = "puc"

    def parse(self, text: str, mask: bool = False) -> dict[str, Any]:
        uppercase_text = text.upper()
        certificate = re.search(
            r"(?:CERTIFICATE|CERT\.?|SL\.?)[ \t]*(?:NO\.?|NUMBER)[ \t]*[:\-]?[ \t]*([A-Z0-9/\-]{6,25})",
            uppercase_text,
        )
        valid = re.search(
            r"VALID\s*(?:UP\s*TO|UPTO|TILL|UNTIL)[^\d]{0,10}(\d{1,2}[/\-.\s][\dA-Z]{1,3}[/\-.\s]\d{4})",
            uppercase_text,
        )
        tested = re.search(
            r"(?:DATE OF TEST|TEST DATE|TESTED ON|DATE)[^\d]{0,10}(\d{1,2}[/\-.\s][\dA-Z]{1,3}[/\-.\s]\d{4})",
            uppercase_text,
        )
        co = re.search(r"\bCO\b[^\d\n]{0,15}(\d+(?:\.\d+)?)", uppercase_text)
        hc = re.search(r"\bHC\b[^\d\n]{0,15}(\d+(?:\.\d+)?)", uppercase_text)
        smoke = re.search(
            r"(?:HSU|SMOKE DENSITY|K\s*VALUE)[^\d\n]{0,15}(\d+(?:\.\d+)?)",
            uppercase_text,
        )
        result = (
            "PASS"
            if re.search(r"\bPASS(?:ED)?\b", uppercase_text)
            else "FAIL"
            if re.search(r"\bFAIL(?:ED)?\b", uppercase_text)
            else None
        )
        fuel = re.search(r"\b(PETROL|DIESEL|CNG|LPG|ELECTRIC)\b", uppercase_text)
        return {
            "vehicle_number": find_vehicle_no(text),
            "certificate_number": certificate.group(1) if certificate else None,
            "test_date": norm_date(tested.group(1)) if tested else None,
            "valid_upto": norm_date(valid.group(1)) if valid else None,
            "fuel_type": fuel.group(1) if fuel else None,
            "co_percent": float(co.group(1)) if co else None,
            "hc_ppm": float(hc.group(1)) if hc else None,
            "smoke_density": float(smoke.group(1)) if smoke else None,
            "result": result,
        }
