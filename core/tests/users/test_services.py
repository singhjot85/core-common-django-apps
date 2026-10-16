from unittest.mock import patch

from django.core.cache import cache

from core.apps.users.services.otp import ConsoleSMSBackend, OTPService
from core.apps.users.services.username import generate_unique_username


class TestUsernameGeneratorService:
    """Tests for username auto-generation strategy."""

    @patch("core.apps.users.get_user_model")
    def test_generate_from_first_and_last_name(self, mock_get_user_model):
        mock_user = mock_get_user_model.return_value
        mock_user.objects.filter.return_value.exists.return_value = False

        username = generate_unique_username(first_name="Jane", last_name="Doe")
        assert username.startswith("jane_doe_")
        assert len(username) > len("jane_doe_")

    @patch("core.apps.users.get_user_model")
    def test_generate_from_email(self, mock_get_user_model):
        mock_user = mock_get_user_model.return_value
        mock_user.objects.filter.return_value.exists.return_value = False

        username = generate_unique_username(email="my.cool.email@example.com")
        assert username.startswith("my_cool_email_")

    @patch("core.apps.users.get_user_model")
    def test_generate_from_phone(self, mock_get_user_model):
        mock_user = mock_get_user_model.return_value
        mock_user.objects.filter.return_value.exists.return_value = False

        username = generate_unique_username(phone_number="+1 (555) 123-4567")
        assert username.startswith("user_")

    @patch("core.apps.users.get_user_model")
    def test_generate_fallback(self, mock_get_user_model):
        mock_user = mock_get_user_model.return_value
        mock_user.objects.filter.return_value.exists.return_value = False

        username = generate_unique_username()
        assert username.startswith("user_")


class TestOTPServiceUnits:
    """Tests for OTP generation, caching, and verification logic."""

    def setup_method(self):
        cache.clear()

    def teardown_method(self):
        cache.clear()

    def test_generate_code_format(self):
        code = OTPService.generate_code(6)
        assert len(code) == 6
        assert code.isdigit()

    def test_hash_code_deterministic(self):
        h1 = OTPService.hash_code("123456")
        h2 = OTPService.hash_code("123456")
        assert h1 == h2
        assert len(h1) == 64

    def test_otp_verification_success(self):
        identifier = "+1234567890"
        code = "654321"
        OTPService.set_otp_cache(identifier, code, timeout=300)

        is_valid, msg = OTPService.verify_otp(identifier, code)
        assert is_valid is True
        assert "verified" in msg.lower()

        # Cache should be invalidated after successful verify
        is_valid2, _ = OTPService.verify_otp(identifier, code)
        assert is_valid2 is False

    def test_otp_verification_invalid_code(self):
        identifier = "+1234567890"
        code = "654321"
        OTPService.set_otp_cache(identifier, code, timeout=300)

        is_valid, msg = OTPService.verify_otp(identifier, "000000")
        assert is_valid is False
        assert "invalid" in msg.lower()

    def test_otp_verification_missing_or_expired(self):
        is_valid, msg = OTPService.verify_otp("+9999999999", "123456")
        assert is_valid is False
        assert "expired" in msg.lower()

    def test_otp_max_attempts_lockout(self):
        identifier = "+1234567890"
        code = "654321"
        OTPService.set_otp_cache(identifier, code, timeout=300)

        # Fail 5 times
        for _ in range(5):
            OTPService.verify_otp(identifier, "999999")

        # 6th attempt should report lockout
        is_valid, msg = OTPService.verify_otp(identifier, code)
        assert is_valid is False
        assert "too many" in msg.lower()

    def test_console_sms_backend(self):
        backend = ConsoleSMSBackend()
        result = backend.send_sms(to="+1234567890", message="Test code: 123456")
        assert result is True
