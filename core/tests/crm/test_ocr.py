"""
Unit and integration tests for Core CRM Document OCR Engine and Celery Beat cron tasks.
"""

import re
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from core.apps.crm import (
    app_settings,
    get_customer_identification_model,
    get_customer_model,
)
from core.apps.crm.constants import IdentityStatusChoices, IdentityTypeChoices
from core.apps.crm.factories import (
    CustomerFactory,
    CustomerIdentificationFactory,
)
from core.apps.crm.services.ocr import (
    InvalidDocumentError,
    classify,
    numeric_value,
    validate_pdf,
)
from core.apps.crm.services.ocr.parsers.aadhaar import AadhaarParser
from core.apps.crm.services.ocr.parsers.insurance import InsuranceParser
from core.apps.crm.services.ocr.parsers.license import DrivingLicenseParser
from core.apps.crm.services.ocr.parsers.puc import PUCCertificateParser
from core.apps.crm.services.ocr.parsers.rc import RegistrationCertificateParser
from core.apps.crm.services.ocr.sanitizer import (
    after_label,
    clean_name,
    clean_text,
    mask_tail,
)
from core.apps.crm.services.ocr.validators import (
    find_dates,
    find_vehicle_no,
    norm_date,
    verhoeff_ok,
)
from core.apps.crm.tasks import (
    process_identification_record,
    process_unverified_identifications_cron,
)

Customer = get_customer_model()
CustomerIdentification = get_customer_identification_model()


class TestOCRValidatorsAndSanitizers:
    """Test pure helper functions in validators and sanitizers."""

    def test_verhoeff_ok(self):
        # 12-digit number with valid Verhoeff checksum: 9999 1234 5678
        assert verhoeff_ok("999912345678") is True
        assert verhoeff_ok("999912345679") is False

    def test_norm_date(self):
        assert norm_date("15/08/1990") == "1990-08-15"
        assert norm_date("15-08-1990") == "1990-08-15"
        assert norm_date("1990-08-15") == "1990-08-15"
        assert norm_date("invalid-date") is None
        assert norm_date(None) is None

    def test_find_dates(self):
        text = "Issued on 10/01/2020 and valid until 09/01/2030."
        dates = find_dates(text)
        assert dates == ["2020-01-10", "2030-01-09"]

    def test_find_vehicle_no(self):
        assert find_vehicle_no("Vehicle: DL-01-AB-1234") == "DL01AB1234"
        assert find_vehicle_no("BH series: 22 BH 1234 AA") == "22BH1234AA"
        assert find_vehicle_no("No plate here") is None

    def test_numeric_value(self):
        match = re.search(r"([\d,]+(?:\.\d+)?)", "IDV: 1,25,000.50")
        assert numeric_value(match) == 125000.50
        assert numeric_value(None) is None

    def test_mask_tail(self):
        assert mask_tail("123456789012", 4) == "XXXXXXXX9012"
        assert mask_tail("1234", 4) == "1234"
        assert mask_tail(None) is None

    def test_clean_name_and_text(self):
        assert clean_name("Name: Jane Doe 123") == "Jane Doe"
        assert clean_name("Father's Name: John Doe") == "John Doe"
        assert clean_name("A") is None
        assert clean_text("  hello   world \n test  ") == "hello world test"

    def test_after_label(self):
        text = "Name: Jane Doe\nAddress: Sector 17, Chandigarh"
        assert after_label(text, [r"Name"]) == "Jane Doe"
        assert after_label(text, [r"Address"]) == "Sector 17, Chandigarh"
        assert after_label(text, [r"Missing"]) is None

    def test_validate_pdf_rejects_non_pdf(self):
        with pytest.raises(InvalidDocumentError, match="not a valid PDF"):
            validate_pdf(b"plain text file")

    def test_validate_pdf_rejects_oversized_file(self):
        large_bytes = b"%PDF-" + b"0" * 15
        with pytest.raises(InvalidDocumentError, match="exceeds maximum"):
            validate_pdf(large_bytes, max_size=10)

    def test_crm_app_settings_and_db_config(self):
        assert app_settings.max_document_upload_size == 10 * 1024 * 1024
        assert app_settings.ocr_native_text_min_chars == 50
        assert app_settings.MAX_DOCUMENT_UPLOAD_SIZE == 10 * 1024 * 1024
        assert app_settings.OCR_NATIVE_TEXT_MIN_CHARS == 50
        config = app_settings.get_crm_config()
        assert "max_document_upload_size" in config
        assert "ocr_native_text_min_chars" in config


class TestOCRClassifiersAndParsers:
    """Test heuristic classification and document-specific parsing."""

    def test_classify_detects_document_types(self):
        assert (
            classify(
                "Government of India Unique Identification Authority of India Aadhaar"
            )
            == "aadhaar"
        )
        assert classify("Union of India Driving Licence DL NO") == "driving_license"
        assert (
            classify("Pollution Under Control Certificate PUCC Emission Test") == "puc"
        )
        assert (
            classify("Certificate of Insurance Motor Insurance Policy Schedule")
            == "insurance"
        )
        assert (
            classify("Certificate of Registration Form 23 Chassis No")
            == "registration_certificate"
        )
        assert classify("Completely unrelated invoice content") == "unknown"

    def test_aadhaar_parser(self):
        text = """
        GOVERNMENT OF INDIA
        Jane Doe
        DOB: 15/08/1990
        FEMALE
        9999 1234 5678
        """
        parser = AadhaarParser()
        raw_data = parser.parse(text)
        assert raw_data["aadhaar_number"] == "999912345678"
        assert raw_data["name"] == "Jane Doe"
        assert raw_data["dob"] == "1990-08-15"
        assert raw_data["gender"] == "FEMALE"

        masked_data = parser.parse(text, mask=True)
        assert masked_data["aadhaar_number"] == "XXXXXXXX5678"

    def test_license_parser(self):
        text = """
        UNION OF INDIA DRIVING LICENCE
        DL-0420110012345
        Name: Jane Doe
        S/D/W of: John Doe
        DOB: 15/08/1990
        Blood Group: O+
        LMV, MCWG
        Address: Sector 17, Chandigarh
        PIN: 160017
        """
        parser = DrivingLicenseParser()
        raw_data = parser.parse(text)
        assert raw_data["license_number"] == "DL04 20110012345"
        assert raw_data["name"] == "Jane Doe"
        assert raw_data["guardian_name"] == "John Doe"
        assert raw_data["dob"] == "1990-08-15"
        assert raw_data["blood_group"] == "O+"
        assert "LMV" in raw_data["vehicle_classes"]
        assert raw_data["pin_code"] == "160017"

        masked_data = parser.parse(text, mask=True)
        assert masked_data["license_number"] == "XXXXXXXXXXXX2345"

    def test_puc_parser(self):
        text = """
        POLLUTION UNDER CONTROL CERTIFICATE
        Vehicle No: DL 01 AB 1234
        Certificate No: PUC123456
        Test Date: 10/01/2023
        Valid Upto: 09/01/2024
        Fuel: PETROL
        CO: 0.15
        HC: 120
        PASS
        """
        parser = PUCCertificateParser()
        data = parser.parse(text, mask=True)
        assert data["vehicle_number"] == "DL01AB1234"
        assert data["certificate_number"] == "PUC123456"
        assert data["test_date"] == "2023-01-10"
        assert data["valid_upto"] == "2024-01-09"
        assert data["fuel_type"] == "PETROL"
        assert data["result"] == "PASS"

    def test_insurance_parser(self):
        text = """
        CERTIFICATE OF INSURANCE
        ABC GENERAL INSURANCE COMPANY LIMITED
        Policy No: POL-987654321
        Insured Name: Jane Doe
        Vehicle No: DL 01 AB 1234
        Chassis No: MA3ER65S001234567
        Engine No: K12MN1234567
        Starts: 01/01/2023
        Expires: 31/12/2023
        IDV: 500,000
        Total Premium: 15,250
        """
        parser = InsuranceParser()
        data = parser.parse(text, mask=True)
        assert data["policy_number"] == "POL-987654321"
        assert data["insured_name"] == "Jane Doe"
        assert data["vehicle_number"] == "DL01AB1234"
        assert data["valid_from"] == "2023-01-01"
        assert data["valid_to"] == "2023-12-31"
        assert data["idv"] == 500000.0
        assert data["total_premium"] == 15250.0

    def test_rc_parser(self):
        text = """
        CERTIFICATE OF REGISTRATION
        Registration No: DL 01 AB 1234
        Owner Name: Jane Doe
        Date of Registration: 15/05/2021
        Valid Upto: 14/05/2036
        Vehicle Class: MOTOR CAR
        Maker: MARUTI SUZUKI
        Model: SWIFT
        Fuel: PETROL
        Chassis No: MA3ER65S001234567
        Engine No: K12MN1234567
        """
        parser = RegistrationCertificateParser()
        data = parser.parse(text, mask=True)
        assert data["registration_number"] == "DL01AB1234"
        assert data["owner_name"] == "Jane Doe"
        assert data["date_of_registration"] == "2021-05-15"
        assert data["registration_valid_upto"] == "2036-05-14"
        assert data["fuel_type"] == "PETROL"


@pytest.mark.django_db
class TestOCRTasksAndBeatCron:
    """Test Celery background execution and Beat cron batch processing."""

    def test_process_identification_record_success(self):
        customer = CustomerFactory(first_name="Jane", last_name="Doe")
        dummy_pdf = SimpleUploadedFile(
            "aadhaar.pdf", b"%PDF-1.4 mock content", content_type="application/pdf"
        )
        identification = CustomerIdentificationFactory(
            customer=customer,
            type=IdentityTypeChoices.AADHAAR,
            document=dummy_pdf,
            status=IdentityStatusChoices.PENDING.value,
        )
        try:
            mock_result = {
                "status": "ok",
                "document_type": "aadhaar",
                "confidence": 0.9,
                "data": {
                    "aadhaar_number": "999912345678",
                    "name": "Jane Doe",
                    "dob": "1990-08-15",
                },
            }

            with patch(
                "core.apps.crm.tasks.process_document", return_value=mock_result
            ):
                success = process_identification_record(identification)

            assert success is True
            identification.refresh_from_db()
            assert identification.status == IdentityStatusChoices.VERIFIED.value
            assert identification.is_verified is True
            assert identification.verified_on == timezone.now().date()
            assert identification.details["aadhaar_number"] == "999912345678"
            assert identification.details["name"] == "Jane Doe"
        finally:
            if identification.document:
                identification.document.delete(save=False)

    def test_process_identification_record_failure(self):
        customer = CustomerFactory(first_name="John", last_name="Doe")
        dummy_pdf = SimpleUploadedFile(
            "doc.pdf", b"%PDF-1.4 empty", content_type="application/pdf"
        )
        identification = CustomerIdentificationFactory(
            customer=customer,
            type=IdentityTypeChoices.AADHAAR,
            document=dummy_pdf,
            status=IdentityStatusChoices.PENDING.value,
        )
        try:
            mock_error = {"status": "error", "error_code": "no_text", "data": {}}
            with patch("core.apps.crm.tasks.process_document", return_value=mock_error):
                success = process_identification_record(identification)

            assert success is False
            identification.refresh_from_db()
            assert (
                identification.status == IdentityStatusChoices.VERIFICATION_FAILED.value
            )
            assert identification.is_verified is False
            assert identification.details.get("error") == "no_text"
        finally:
            if identification.document:
                identification.document.delete(save=False)

    def test_process_unverified_identifications_cron_batch(self):
        customer = CustomerFactory(first_name="Batch", last_name="User")
        dummy_pdf1 = SimpleUploadedFile(
            "doc1.pdf", b"%PDF-1.4 doc1", content_type="application/pdf"
        )
        dummy_pdf2 = SimpleUploadedFile(
            "doc2.pdf", b"%PDF-1.4 doc2", content_type="application/pdf"
        )

        id1 = CustomerIdentificationFactory(
            customer=customer,
            type=IdentityTypeChoices.DRIVING_LICENSE,
            document=dummy_pdf1,
            status=IdentityStatusChoices.PENDING.value,
        )
        id2 = CustomerIdentificationFactory(
            customer=customer,
            type=IdentityTypeChoices.AADHAAR,
            document=dummy_pdf2,
            status=IdentityStatusChoices.PENDING.value,
        )
        try:
            mock_ok = {
                "status": "ok",
                "document_type": "driving_license",
                "confidence": 0.85,
                "data": {"license_number": "DL-1234"},
            }

            with patch("core.apps.crm.tasks.process_document", return_value=mock_ok):
                stats = process_unverified_identifications_cron(batch_size=10)

            assert stats["total"] >= 2
            assert stats["verified"] >= 2
            id1.refresh_from_db()
            id2.refresh_from_db()
            assert id1.status == IdentityStatusChoices.VERIFIED.value
            assert id2.status == IdentityStatusChoices.VERIFIED.value
        finally:
            for ident in (id1, id2):
                if ident.document:
                    ident.document.delete(save=False)
