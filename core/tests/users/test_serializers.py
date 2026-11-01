from unittest.mock import patch

import pytest
from django.test import override_settings

from core.apps.crm import get_customer_model
from core.apps.users import get_user_model
from core.apps.users.api.serializers import (
    EmailOTPSignupSerializer,
    GoogleLoginSerializer,
    LoginSerializer,
    OTPSendSerializer,
    OTPVerifySerializer,
    PhoneOTPLoginSerializer,
    PhoneOTPSendSerializer,
    PhoneOTPSignupSerializer,
    SignupSerializer,
)
from core.apps.users.constants import OTPChannelChoices, OTPPurposeChoices

User = get_user_model()
Customer = get_customer_model()


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
            "phone_number": "+12025550123",
        }
        serializer = SignupSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    @patch.object(User.objects, "filter")
    def test_signup_validation_duplicate_phone_rejected(self, mock_filter):
        mock_filter.return_value.exists.return_value = True
        data = {
            "first_name": "Alice",
            "last_name": "Smith",
            "username": "alice_smith",
            "password": "Password123!",  # pragma: allowlist secret
            "phone_number": "+12025550123",
        }
        serializer = SignupSerializer(data=data)
        assert not serializer.is_valid()
        assert "phone_number" in serializer.errors

    @patch.object(User.objects, "filter")
    def test_signup_validation_invalid_phone_rejected(self, mock_filter):
        mock_filter.return_value.exists.return_value = False
        data = {
            "first_name": "Alice",
            "last_name": "Smith",
            "username": "alice_smith",
            "password": "Password123!",  # pragma: allowlist secret
            "phone_number": "invalid-phone",
        }
        serializer = SignupSerializer(data=data)
        assert not serializer.is_valid()
        assert "phone_number" in serializer.errors

    @patch.object(User.objects, "filter")
    def test_signup_validation_blank_phone_normalized_to_none(self, mock_filter):
        mock_filter.return_value.exists.return_value = False
        data = {
            "first_name": "Alice",
            "last_name": "Smith",
            "username": "alice_smith",
            "password": "Password123!",  # pragma: allowlist secret
            "phone_number": "",
        }
        serializer = SignupSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data.get("phone_number") is None


class TestOTPSerializers:
    """Tests for OTP serializers validation."""

    def test_otp_send_phone_valid(self):
        data = {
            "identifier": "+1 202 555 0123",
            "channel": OTPChannelChoices.PHONE,
            "purpose": OTPPurposeChoices.LOGIN,
        }
        serializer = OTPSendSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["identifier"] == "+12025550123"

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
            "identifier": "+1 202 555 0123",
            "code": "123456",
            "channel": OTPChannelChoices.PHONE,
        }
        serializer = OTPVerifySerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["identifier"] == "+12025550123"


class TestPhoneOTPSerializers:
    """Tests for phone-specific OTP serializers ensuring E.164 normalization."""

    @patch("core.apps.users.api.serializers.base.queue_task")
    def test_phone_otp_send_serializer_queues_e164(self, mock_queue_task):
        data = {
            "phone_number": "+1 202 555 0123",
            "purpose": OTPPurposeChoices.LOGIN,
        }
        serializer = PhoneOTPSendSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.send() is True
        mock_queue_task.assert_called_once()
        _, kwargs = mock_queue_task.call_args
        assert kwargs["task_kwargs"]["identifier"] == "+12025550123"

    @patch.object(User.objects, "filter")
    @patch("core.apps.users.api.serializers.base.OTPServiceFactory.verify_otp")
    def test_phone_otp_signup_serializer_verifies_e164(
        self, mock_verify_otp, mock_filter
    ):
        mock_filter.return_value.exists.return_value = False
        mock_verify_otp.return_value = (True, "OTP verified successfully.")
        data = {
            "first_name": "Bob",
            "phone_number": "+1 202 555 0123",
            "otp_code": "123456",
        }
        serializer = PhoneOTPSignupSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        mock_verify_otp.assert_called_once_with(
            identifier="+12025550123", code="123456"
        )
        assert serializer.validated_data["is_phone_verified"] is True

    @patch("core.apps.users.api.serializers.base.OTPServiceFactory.verify_otp")
    def test_phone_otp_login_serializer_verifies_e164(self, mock_verify_otp):
        mock_verify_otp.return_value = (True, "OTP verified successfully.")
        user = User(
            username="bob",
            phone_number="+12025550123",
            is_active=True,
            is_phone_verified=True,
        )
        with patch.object(User.objects, "filter") as mock_filter:
            mock_filter.return_value.first.return_value = user
            data = {
                "phone_number": "+1 202 555 0123",
                "otp_code": "123456",
            }
            serializer = PhoneOTPLoginSerializer(data=data)
            assert serializer.is_valid(), serializer.errors
            mock_verify_otp.assert_called_once_with(
                identifier="+12025550123", code="123456"
            )
            assert serializer.validated_data["user"] == user


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


@pytest.mark.django_db
class TestLoginSerializer:
    """Tests for LoginSerializer credentials verification, whitespace preservation, and zero enumeration."""

    def test_login_serializer_valid_credentials(self):
        """Active user with correct credentials validates successfully."""
        user = User.objects.create_user(
            username="valid_login_user",
            email="valid@example.com",
            password="MyPassword123!",  # pragma: allowlist secret
            is_active=True,
        )
        serializer = LoginSerializer(
            data={
                "username": "valid_login_user",
                "password": "MyPassword123!",  # pragma: allowlist secret
            }
        )
        assert serializer.is_valid()
        assert serializer.validated_data["user"] == user

    def test_login_serializer_trims_password_whitespace(self):
        """Password containing whitespace is trimmed to authenticate against trimmed password."""
        user = User.objects.create_user(
            username="space_login_user",
            password="SpacePass123!",  # pragma: allowlist secret
            is_active=True,
        )
        serializer = LoginSerializer(
            data={"username": "space_login_user", "password": "  SpacePass123!  "}
        )
        assert serializer.is_valid()
        assert serializer.validated_data["user"] == user

    def test_login_serializer_blank_fields_raise_flat_error(self):
        """Blank username and password should raise flat error messages without nested dicts."""
        serializer = LoginSerializer(data={"username": "   ", "password": ""})
        assert not serializer.is_valid()
        errors = serializer.errors
        assert "username" in errors
        assert "password" in errors
        # Ensure errors are flat list/string, not nested dict
        assert not isinstance(errors["username"][0], dict)
        assert not isinstance(errors["password"][0], dict)

    def test_login_serializer_wrong_password_returns_generic_error(self):
        """Incorrect password returns generic error message."""
        User.objects.create_user(
            username="wrong_pass_user",
            password="CorrectPassword123!",  # pragma: allowlist secret
            is_active=True,
        )
        serializer = LoginSerializer(
            data={
                "username": "wrong_pass_user",
                "password": "BadPassword",  # pragma: allowlist secret
            }
        )
        assert not serializer.is_valid()
        assert (
            LoginSerializer.USER_NOT_FOUND_ERROR
            in serializer.errors["non_field_errors"]
        )

    def test_login_serializer_inactive_user_with_wrong_password_does_not_leak_status(
        self,
    ):
        """Inactive user with incorrect password receives generic error (no account enumeration)."""
        User.objects.create_user(
            username="disabled_user",
            password="CorrectPassword123!",  # pragma: allowlist secret
            is_active=False,
        )
        serializer = LoginSerializer(
            data={
                "username": "disabled_user",
                "password": "WrongPassword",  # pragma: allowlist secret
            }
        )
        assert not serializer.is_valid()
        # Must return generic error, NOT "This account is disabled."
        assert (
            LoginSerializer.USER_NOT_FOUND_ERROR
            in serializer.errors["non_field_errors"]
        )

    def test_login_serializer_inactive_user_with_correct_password_reports_disabled(
        self,
    ):
        """Inactive user with correct password reports that the account is disabled."""
        User.objects.create_user(
            username="disabled_user_auth",
            password="CorrectPassword123!",  # pragma: allowlist secret
            is_active=False,
        )
        serializer = LoginSerializer(
            data={
                "username": "disabled_user_auth",
                "password": "CorrectPassword123!",  # pragma: allowlist secret
            }
        )
        assert not serializer.is_valid()
        assert "disabled" in str(serializer.errors["non_field_errors"][0]).lower()


@pytest.mark.django_db
class TestSignupCustomerAutoCreation:
    """Integration tests verifying automatic CRM Customer provisioning upon user signup."""

    def test_signup_auto_creates_customer_profile_and_primary_contacts(self):
        """SignupSerializer provisions a Customer profile with primary phone and email."""
        data = {
            "first_name": "Rosalind",
            "last_name": "Franklin",
            "username": "rfranklin",
            "email": "rosalind@example.com",
            "phone_number": "+12025550199",
            "password": "StrongPassword123!",  # pragma: allowlist secret
        }
        serializer = SignupSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        user = serializer.save()

        assert Customer.objects.filter(user=user).exists()
        customer = Customer.objects.get(user=user)
        assert customer.first_name == "Rosalind"
        assert customer.last_name == "Franklin"
        assert customer.is_active is True

        primary_phone = customer.primary_phone
        assert primary_phone is not None
        assert str(primary_phone.phone) == "+12025550199"
        assert primary_phone.is_primary is True
        assert primary_phone.is_verified is False

        primary_email = customer.primary_email
        assert primary_email is not None
        assert primary_email.email == "rosalind@example.com"
        assert primary_email.is_primary is True
        assert primary_email.is_verified is False

    @override_settings(CORE_USERS_SETTINGS={"AUTO_CREATE_CUSTOMER": False})
    def test_signup_respects_auto_create_customer_flag_disabled(self):
        """When AUTO_CREATE_CUSTOMER is False, no customer profile is created."""
        data = {
            "first_name": "Dorothy",
            "last_name": "Hodgkin",
            "username": "dhodgkin",
            "email": "dorothy@example.com",
            "phone_number": "+12025550188",
            "password": "StrongPassword123!",  # pragma: allowlist secret
        }
        serializer = SignupSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        user = serializer.save()

        assert not Customer.objects.filter(user=user).exists()

    @patch("core.apps.users.api.serializers.base.OTPServiceFactory.verify_otp")
    def test_email_otp_signup_auto_creates_customer_with_verified_email(
        self, mock_verify_otp
    ):
        """EmailOTPSignupSerializer marks customer primary email as verified."""
        mock_verify_otp.return_value = (True, "OTP verified successfully")

        data = {
            "first_name": "Chien-Shiung",
            "last_name": "Wu",
            "username": "cswu",
            "email": "wu@example.com",
            "otp_code": "123456",
            "password": "StrongPassword123!",  # pragma: allowlist secret
        }
        serializer = EmailOTPSignupSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        user = serializer.save()

        customer = Customer.objects.get(user=user)
        primary_email = customer.primary_email
        assert primary_email is not None
        assert primary_email.is_verified is True

    @patch("core.apps.users.api.serializers.base.OTPServiceFactory.verify_otp")
    def test_phone_otp_signup_auto_creates_customer_with_verified_phone(
        self, mock_verify_otp
    ):
        """PhoneOTPSignupSerializer marks customer primary phone as verified."""
        mock_verify_otp.return_value = (True, "OTP verified successfully")

        data = {
            "first_name": "Lise",
            "last_name": "Meitner",
            "username": "lmeitner",
            "phone_number": "+12025550177",
            "otp_code": "123456",
            "password": "StrongPassword123!",  # pragma: allowlist secret
        }
        serializer = PhoneOTPSignupSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        user = serializer.save()

        customer = Customer.objects.get(user=user)
        primary_phone = customer.primary_phone
        assert primary_phone is not None
        assert primary_phone.is_verified is True
