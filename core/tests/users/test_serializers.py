from unittest.mock import patch

from core.apps.users import get_user_model
from core.apps.users.api.serializers import (
    GoogleLoginSerializer,
    OTPSendSerializer,
    OTPVerifySerializer,
    SignupSerializer,
)
from core.apps.users.constants import OTPChannelChoices, OTPPurposeChoices

User = get_user_model()


class TestSignupSerializer:
    """Tests for SignupSerializer validation logic."""

    @patch.object(User.objects, "filter")
    def test_signup_validation_success_full(self, mock_filter):
        mock_filter.return_value.exists.return_value = False
        data = {
            "first_name": "Alice",
            "last_name": "Smith",
            "username": "alice_smith",
            "password": "Password123!",  # pragma: allowlist secret
            "email": "alice@example.com",
            "phone_number": "+1234567890",
        }
        serializer = SignupSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    @patch.object(User.objects, "filter")
    def test_signup_validation_success_phone_only_no_password(self, mock_filter):
        mock_filter.return_value.exists.return_value = False
        data = {
            "first_name": "Bob",
            "phone_number": "+1987654321",
        }
        serializer = SignupSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data.get("password") == ""
        assert serializer.validated_data.get("username") == ""

    @patch.object(User.objects, "filter")
    def test_signup_validation_success_email_only(self, mock_filter):
        mock_filter.return_value.exists.return_value = False
        data = {
            "email": "bob@example.com",
        }
        serializer = SignupSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_signup_validation_fails_no_identifiers(self):
        data = {
            "first_name": "Bob",
            "last_name": "Builder",
        }
        serializer = SignupSerializer(data=data)
        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors


class TestOTPSerializers:
    """Tests for OTP serializers validation."""

    def test_otp_send_phone_valid(self):
        data = {
            "identifier": "+1 (555) 019-2834",
            "channel": OTPChannelChoices.PHONE,
            "purpose": OTPPurposeChoices.LOGIN,
        }
        serializer = OTPSendSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_otp_send_phone_invalid_length(self):
        data = {
            "identifier": "123",
            "channel": OTPChannelChoices.PHONE,
        }
        serializer = OTPSendSerializer(data=data)
        assert not serializer.is_valid()
        assert "identifier" in serializer.errors

    def test_otp_send_email_valid(self):
        data = {
            "identifier": "test.user@example.com",
            "channel": OTPChannelChoices.EMAIL,
        }
        serializer = OTPSendSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_otp_send_email_invalid(self):
        data = {
            "identifier": "not-an-email",
            "channel": OTPChannelChoices.EMAIL,
        }
        serializer = OTPSendSerializer(data=data)
        assert not serializer.is_valid()
        assert "identifier" in serializer.errors

    def test_otp_verify_serializer_valid(self):
        data = {
            "identifier": "+1234567890",
            "code": "123456",
            "channel": OTPChannelChoices.PHONE,
        }
        serializer = OTPVerifySerializer(data=data)
        assert serializer.is_valid(), serializer.errors


class TestGoogleLoginSerializer:
    """Tests for GoogleLoginSerializer."""

    def test_google_login_serializer_valid(self):
        data = {"id_token": "mock-google-id-token-xyz"}
        serializer = GoogleLoginSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_google_login_serializer_empty_invalid(self):
        data = {"id_token": ""}
        serializer = GoogleLoginSerializer(data=data)
        assert not serializer.is_valid()
