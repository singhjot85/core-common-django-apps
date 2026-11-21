"""
Registration Certificate (RC) document parser implementation.
"""

import re
from typing import Any

from ..sanitizer import after_label, clean_name
from ..validators import find_vehicle_no, norm_date
from .base import BaseDocumentParser


class RegistrationCertificateParser(BaseDocumentParser):
    """
    Parser for Indian Motor Vehicle Registration Certificates (RC).
    """

    doc_type = "registration_certificate"

    def parse(self, text: str, mask: bool = False) -> dict[str, Any]:
        uppercase_text = text.upper()
        date_pattern = r"(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{4})"
        registration_date = re.search(
            r"DATE OF REGISTRATION[^\d]{0,10}" + date_pattern, uppercase_text
        )
        valid = re.search(
            r"VALID\s*(?:UP\s*TO|UPTO|TILL)[^\d]{0,10}" + date_pattern, uppercase_text
        )
        manufacture = re.search(r"MFG[^\d\n]{0,20}(\d{2}/\d{4}|\d{4})", uppercase_text)
        chassis = re.search(
            r"CHASSIS\s*(?:NO\.?|NUMBER)?\s*[:\-]?\s*([A-Z0-9]{10,20})",
            uppercase_text,
        )
        engine = re.search(
            r"ENGINE\s*(?:NO\.?|NUMBER)\s*[:\-]?\s*([A-Z0-9]{6,20})",
            uppercase_text,
        )
        fuel = re.search(r"\b(PETROL|DIESEL|CNG|LPG|ELECTRIC)\b", uppercase_text)

        def uppercase(value: str | None) -> str | None:
            return re.sub(r"\s+", " ", value).strip().upper() if value else None

        return {
            "registration_number": find_vehicle_no(text),
            "owner_name": clean_name(after_label(text, [r"Owner(?:'s)? Name"])),
            "guardian_name": clean_name(
                after_label(text, [r"S/?W/?D\s*of", r"Son/Wife/Daughter of"])
            ),
            "address": uppercase(after_label(text, [r"Address"])),
            "date_of_registration": (
                norm_date(registration_date.group(1)) if registration_date else None
            ),
            "registration_valid_upto": norm_date(valid.group(1)) if valid else None,
            "vehicle_class": uppercase(after_label(text, [r"Vehicle Class"])),
            "maker": uppercase(after_label(text, [r"Maker"])),
            "model": uppercase(after_label(text, [r"Model"])),
            "fuel_type": fuel.group(1) if fuel else None,
            "colour": uppercase(after_label(text, [r"Colou?r"])),
            "manufacture_date": manufacture.group(1) if manufacture else None,
            "chassis_number": chassis.group(1) if chassis else None,
            "engine_number": engine.group(1) if engine else None,
        }
