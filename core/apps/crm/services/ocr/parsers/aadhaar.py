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

    def _extract_aadhaar_number(self, text: str, mask: bool = False) -> str | None:
        """Find and validate 12-digit Aadhaar number using Verhoeff checksum."""
        raw_candidates = re.findall(r"\b(\d{4}\s\d{4}\s\d{4})\b", text)
        if raw_candidates:
            candidates = [
                c.replace(" ", "")
                for c in raw_candidates
                if verhoeff_ok(c.replace(" ", ""))
            ]
        else:
            candidates = [
                c for c in re.findall(r"\b(\d{12})\b", text) if verhoeff_ok(c)
            ]

        if not candidates:
            return None
        return mask_tail(candidates[0], 4) if mask else candidates[0]

    def _extract_dob_and_yob(self, text: str) -> tuple[str | None, int | None]:
        """Extract date of birth or year of birth."""
        dob_match = re.search(
            r"(?:DOB|Date of Birth|जन्म\s*तारीख|जन्म\s*तिथि)\s*[:\-]?\s*(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{4})",
            text,
            re.I,
        )
        dob = norm_date(dob_match.group(1)) if dob_match else None
        if dob:
            return dob, None

        yob_match = re.search(r"(?:Year of Birth|YOB)\s*[:\-]?\s*(\d{4})", text, re.I)
        yob = int(yob_match.group(1)) if yob_match else None
        return None, yob

    def _extract_name(self, text: str) -> str | None:
        """Extract person name appearing before DOB or after name label."""
        lines = [clean_text(line) for line in text.splitlines() if clean_text(line)]
        for index, line in enumerate(lines):
            if re.search(r"DOB|Date of Birth|Year of Birth|जन्म", line, re.I) and index:
                candidate = clean_name(lines[index - 1])
                if (
                    candidate
                    and len(candidate) > 2
                    and not re.search(r"GOVERNMENT|INDIA|AADHAAR", candidate)
                ):
                    return candidate

        return clean_name(after_label(text, [r"Name", r"नाम"]))

    def parse(self, text: str, mask: bool = False) -> dict[str, Any]:
        """
        Parse Aadhaar card text and extract structured KYC fields.

        Args:
            text (str): Document text block.
            mask (bool): Optional flag to mask sensitive Aadhaar number. Defaults to False.

        Returns:
            dict[str, Any]: Extracted document fields.
        """
        dob, yob = self._extract_dob_and_yob(text)
        gender_match = re.search(r"\b(MALE|FEMALE|TRANSGENDER)\b", text, re.I)

        return {
            "aadhaar_number": self._extract_aadhaar_number(text, mask=mask),
            "name": self._extract_name(text),
            "gender": gender_match.group(1).upper() if gender_match else None,
            "dob": dob,
            "year_of_birth": yob,
        }
