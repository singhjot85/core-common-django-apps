"""
Aadhaar KYC document parser implementation.
"""

import re
from typing import Any

from ..sanitizer import after_label, clean_name, clean_text, mask_tail
from ..validators import norm_date, verhoeff_ok
from .base import BaseDocumentParser


class AadhaarParser(BaseDocumentParser):
    """
    Parser for Indian UIDAI Aadhaar cards.
    """

    doc_type = "aadhaar"

    def parse(self, text: str, mask: bool = True) -> dict[str, Any]:
        output: dict[str, Any] = {
            "aadhaar_number": None,
            "name": None,
            "gender": None,
            "dob": None,
            "year_of_birth": None,
        }

        raw_candidates = re.findall(r"\b(\d{4}\s\d{4}\s\d{4})\b", text)
        if not raw_candidates:
            raw_candidates = re.findall(r"\b(\d{12})\b", text)
            candidates = [c for c in raw_candidates if verhoeff_ok(c)]
        else:
            candidates = [
                c.replace(" ", "")
                for c in raw_candidates
                if verhoeff_ok(c.replace(" ", ""))
            ]

        if candidates:
            output["aadhaar_number"] = (
                mask_tail(candidates[0], 4) if mask else candidates[0]
            )

        dob = re.search(
            r"(?:DOB|Date of Birth|जन्म\s*तारीख|जन्म\s*तिथि)\s*[:\-]?\s*(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{4})",
            text,
            re.I,
        )
        output["dob"] = norm_date(dob.group(1)) if dob else None
        if not output["dob"]:
            year_of_birth = re.search(
                r"(?:Year of Birth|YOB)\s*[:\-]?\s*(\d{4})", text, re.I
            )
            output["year_of_birth"] = (
                int(year_of_birth.group(1)) if year_of_birth else None
            )

        gender = re.search(r"\b(MALE|FEMALE|TRANSGENDER)\b", text, re.I)
        output["gender"] = gender.group(1).upper() if gender else None

        lines = [clean_text(line) for line in text.splitlines() if clean_text(line)]
        name = None
        for index, line in enumerate(lines):
            if re.search(r"DOB|Date of Birth|Year of Birth|जन्म", line, re.I) and index:
                candidate = clean_name(lines[index - 1])
                if (
                    candidate
                    and len(candidate) > 2
                    and not re.search(r"GOVERNMENT|INDIA|AADHAAR", candidate)
                ):
                    name = candidate
                    break

        if not name:
            name = clean_name(after_label(text, [r"Name", r"नाम"]))

        output["name"] = name
        return output
