"""
Driving License document parser implementation.
"""

import re
from typing import Any

from ..sanitizer import after_label, clean_name, clean_text, mask_tail
from ..validators import find_dates, norm_date
from .base import BaseDocumentParser

_DL_RE = re.compile(r"\b([A-Z]{2})[\s-]?(\d{2})[\s-]?((?:19|20)\d{2})[\s-]?(\d{7})\b")


class DrivingLicenseParser(BaseDocumentParser):
    """
    Parser for Indian State Driving Licenses.
    """

    doc_type = "driving_license"

    def parse(self, text: str, mask: bool = True) -> dict[str, Any]:
        uppercase_text = text.upper()
        match = _DL_RE.search(uppercase_text)
        license_number = "".join(match.groups()) if match else None
        formatted_number = (
            f"{match.group(1)}{match.group(2)} {match.group(3)}{match.group(4)}"
            if match
            else None
        )
        dob = re.search(
            r"(?:DOB|DATE OF BIRTH)[^\d]{0,15}(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{4})",
            uppercase_text,
        )
        issue = re.search(
            r"(?:DATE OF (?:FIRST )?ISSUE|DOI|ISSUE DATE)[^\d]{0,15}(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{4})",
            uppercase_text,
        )
        valid_non_transport = re.search(
            r"(?:VALID(?:ITY)?\s*\(?NT\)?|NON[- ]?TRANSPORT)[^\d]{0,20}(?:TILL|UPTO|TO)?[^\d]{0,10}(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{4})",
            uppercase_text,
        )
        valid_transport = re.search(
            r"(?:VALID(?:ITY)?\s*\(?TR\)?|\bTRANSPORT\b)[^\d]{0,20}(?:TILL|UPTO|TO)?[^\d]{0,10}(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{4})",
            uppercase_text,
        )
        blood = re.search(
            r"BLOOD\s*GROUP\s*[:\-]?\s*(AB|A|B|O)\s*([+-]|POS(?:ITIVE)?|NEG(?:ATIVE)?)",
            uppercase_text,
        )
        classes = re.findall(
            r"\b(MCWG|MCWOG|LMV(?:-NT|-TR)?|HMV|HGMV|HPMV|TRANS|LMV|MGV|FVG|TRCTR|M\.?CYCL)\b",
            uppercase_text,
        )

        output: dict[str, Any] = {
            "license_number": (
                mask_tail(formatted_number, 4)
                if mask and formatted_number
                else formatted_number
            ),
            "name": clean_name(after_label(text, [r"\bName"])),
            "guardian_name": clean_name(
                after_label(
                    text, [r"S/?D/?W\s*of", r"Son/Daughter/Wife of", r"Father'?s? Name"]
                )
            ),
            "dob": norm_date(dob.group(1)) if dob else None,
            "date_of_issue": norm_date(issue.group(1)) if issue else None,
            "valid_upto_non_transport": (
                norm_date(valid_non_transport.group(1)) if valid_non_transport else None
            ),
            "valid_upto_transport": (
                norm_date(valid_transport.group(1)) if valid_transport else None
            ),
            "blood_group": (
                blood.group(1)
                + (
                    "+"
                    if blood.group(2) in ("+", "POS") or blood.group(2).startswith("P")
                    else "-"
                )
                if blood
                else None
            ),
            "vehicle_classes": sorted(set(classes)),
            "address": clean_text(after_label(text, [r"Address", r"\bAdd\b"]) or "")
            or None,
            "pin_code": (
                re.search(r"\b[1-9]\d{5}\b", text).group(0)
                if re.search(r"\b[1-9]\d{5}\b", text)
                else None
            ),
            "state_code": license_number[:2] if license_number else None,
        }
        if not output["dob"]:
            dates = sorted(find_dates(text))
            output["dob"] = dates[0] if dates else None
        return output
