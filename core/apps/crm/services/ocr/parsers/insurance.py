"""
Vehicle Insurance document parser implementation.
"""

import re
from typing import Any

from ..sanitizer import after_label, clean_name
from ..validators import find_vehicle_no, norm_date
from .base import BaseDocumentParser


class InsuranceParser(BaseDocumentParser):
    """
    Parser for Indian Motor Vehicle Insurance certificates and policy schedules.
    """

    doc_type = "insurance"

    def parse(self, text: str, mask: bool = True) -> dict[str, Any]:
        uppercase_text = text.upper()
        policy = re.search(
            r"POLICY\s*(?:NO\.?|NUMBER|#)\s*[:\-]?\s*([A-Z0-9/\-]{6,30})",
            uppercase_text,
        )
        valid_from = re.search(
            r"(?:FROM|START(?:S)?(?: DATE)?|INCEPTION)[^\d]{0,15}(\d{1,2}[/\-.\s][\dA-Z]{1,3}[/\-.\s]\d{4})",
            uppercase_text,
        )
        valid_to = re.search(
            r"(?:TO|EXPIR(?:Y|ES)(?: DATE)?|VALID (?:UP)?TO|END DATE|MIDNIGHT OF)[^\d]{0,15}(\d{1,2}[/\-.\s][\dA-Z]{1,3}[/\-.\s]\d{4})",
            uppercase_text,
        )
        idv = re.search(r"IDV[^\d]{0,25}([\d,]+(?:\.\d+)?)", uppercase_text)
        premium = re.search(
            r"(?:TOTAL\s*)?PREMIUM[^\d]{0,25}([\d,]+(?:\.\d+)?)", uppercase_text
        )
        chassis = re.search(
            r"CHASSIS\s*(?:NO\.?|NUMBER)?\s*[:\-]?\s*([A-Z0-9]{10,20})",
            uppercase_text,
        )
        engine = re.search(
            r"ENGINE\s*(?:NO\.?|NUMBER)?\s*[:\-]?\s*([A-Z0-9]{6,20})",
            uppercase_text,
        )
        insurer = re.search(
            r"([A-Z][A-Z &.]{3,40}(?:GENERAL INSURANCE|INSURANCE CO(?:MPANY)?\.?(?: LTD\.?| LIMITED)?|ASSURANCE))",
            uppercase_text,
        )
        if "COMPREHENSIVE" in uppercase_text or "PACKAGE" in uppercase_text:
            policy_type = "COMPREHENSIVE"
        elif re.search(r"THIRD[\s-]*PARTY|LIABILITY ONLY", uppercase_text):
            policy_type = "THIRD_PARTY"
        else:
            policy_type = None

        def numeric_value(match: re.Match[str] | None) -> float | None:
            return float(match.group(1).replace(",", "")) if match else None

        return {
            "policy_number": policy.group(1) if policy else None,
            "insurer": (
                re.sub(r"\s+", " ", insurer.group(1)).strip() if insurer else None
            ),
            "policy_type": policy_type,
            "insured_name": clean_name(
                after_label(text, [r"Insured(?: Name)?", r"Name of (?:the )?Insured"])
            ),
            "vehicle_number": find_vehicle_no(text),
            "chassis_number": chassis.group(1) if chassis else None,
            "engine_number": engine.group(1) if engine else None,
            "valid_from": norm_date(valid_from.group(1)) if valid_from else None,
            "valid_to": norm_date(valid_to.group(1)) if valid_to else None,
            "idv": numeric_value(idv),
            "total_premium": numeric_value(premium),
        }
