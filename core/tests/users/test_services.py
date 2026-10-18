from unittest.mock import MagicMock, patch

import pytest
from django.core.cache import cache
from django.core.exceptions import ValidationError

from core.apps.users import get_otp_log_model, get_social_account_model, get_user_model
from core.apps.users.constants import (
    OTPChannelChoices,
    OTPDeliveryStatusChoices,
    OTPPurposeChoices,
    SocialProviderChoices,
)
from core.apps.users.services.otp import (
    BaseOTPService,
    EmailOTPService,
    OTPService,
    OTPServiceFactory,
    PhoneOTPService,
)
from core.apps.users.services.social import GoogleAuthService, SocialAuthServiceFactory
from core.apps.users.tasks import create_otp_log_task, send_otp_task
from core.utils.backends.sms import BaseSMSBackend, ConsoleSMSBackend
from core.utils.generators.username import UsernameGenerator, generate_unique_username

User = get_user_model()
SocialAccount = get_social_account_model()
OTPLog = get_otp_log_model()


class TestUsernameGeneratorService:
    """Tests for UsernameGenerator class and auto-generation strategy."""

    def test_generator_class_instantiation(self):
        generator = UsernameGenerator(
            first_name="John",
            last_name="Smith",
            email="john@example.com",
            phone_number="+1555123456",
        )
        assert generator.first_name == "John"
        assert generator.last_name == "Smith"
        assert generator.build_base_slug() == "john_smith"

    def test_generate_from_first_and_last_name(self):
        mock_user = MagicMock()
        mock_user.objects.filter.return_value.exists.return_value = False

        username = generate_unique_username(
            first_name="Jane", last_name="Doe", user_model=mock_user
        )
        assert username.startswith("jane_doe_")
        assert len(username) > len("jane_doe_")

    def test_generate_from_email(self):
        mock_user = MagicMock()
        mock_user.objects.filter.return_value.exists.return_value = False

        generator = UsernameGenerator(email="my.cool.email@example.com")
        username = generator.generate(user_model=mock_user)
        assert username.startswith("my_cool_email_")

    def test_generate_from_phone(self):
        mock_user = MagicMock()
        mock_user.objects.filter.return_value.exists.return_value = False

        username = generate_unique_username(
            phone_number="+1 (555) 123-4567", user_model=mock_user
        )
        assert username.startswith("user_")

    def test_generate_fallback(self):
        mock_user = MagicMock()
        mock_user.objects.filter.return_value.exists.return_value = False

        username = generate_unique_username(user_model=mock_user)
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


class TestPhoneAndEmailOTPServices:
    """Tests for channel-specific OTP template implementations."""

    @patch.object(User.objects, "filter")
    def test_phone_otp_check_user_exists(self, mock_filter):
        service = PhoneOTPService()
        mock_filter.return_value.exists.return_value = True
        assert service.check_user_exists("+1555123456") is True

        mock_filter.return_value.exists.return_value = False
        assert service.check_user_exists("+1555999999") is False

    @patch("core.apps.users.services.otp.sms.app_settings")
    def test_phone_otp_deliver(self, mock_settings):
        mock_backend = MagicMock()
        mock_backend.return_value.send_sms.return_value = True
        mock_settings.SMS_BACKEND = mock_backend

        service = PhoneOTPService()
        result = service.deliver(
            identifier="+1555123456", code="123456", message="Code: 123456"
        )
        assert result is True
        mock_backend.return_value.send_sms.assert_called_once_with(
            to="+1555123456", message="Code: 123456"
        )

    @patch.object(User.objects, "filter")
    def test_email_otp_check_user_exists(self, mock_filter):
        service = EmailOTPService()
        mock_filter.return_value.exists.return_value = True
        assert service.check_user_exists("test@example.com") is True

        mock_filter.return_value.exists.return_value = False
        assert service.check_user_exists("nobody@example.com") is False

    @patch("core.apps.users.services.otp.email.send_mail")
    def test_email_otp_deliver_success(self, mock_send_mail):
        service = EmailOTPService()
        result = service.deliver(
            identifier="test@example.com", code="123456", message="Code: 123456"
        )
        assert result is True
        mock_send_mail.assert_called_once()

    @patch("core.apps.users.services.otp.email.send_mail")
    def test_email_otp_deliver_failure(self, mock_send_mail):
        mock_send_mail.side_effect = Exception("SMTP connection failure")
        service = EmailOTPService()
        result = service.deliver(
            identifier="test@example.com", code="123456", message="Code: 123456"
        )
        assert result is False


class TestOTPServiceFactory:
    """Tests for OTPServiceFactory strategy dispatch."""

    def test_get_service_phone(self):
        service = OTPServiceFactory.get_service(OTPChannelChoices.PHONE)
        assert isinstance(service, PhoneOTPService)

    def test_get_service_email(self):
        service = OTPServiceFactory.get_service(OTPChannelChoices.EMAIL)
        assert isinstance(service, EmailOTPService)

    def test_get_service_unsupported(self):
        with pytest.raises(ValueError, match="Unsupported OTP delivery channel"):
            OTPServiceFactory.get_service("carrier_pigeon")

    @patch.object(PhoneOTPService, "send_otp")
    def test_send_otp_dispatch(self, mock_send_otp):
        mock_send_otp.return_value = True
        result = OTPServiceFactory.send_otp(
            identifier="+1555123456",
            channel=OTPChannelChoices.PHONE,
            purpose=OTPPurposeChoices.LOGIN,
        )
        assert result is True
        mock_send_otp.assert_called_once_with(
            identifier="+1555123456", purpose=OTPPurposeChoices.LOGIN
        )


class TestSocialAuthServices:
    """Tests for social authentication service strategies."""

    def test_google_auth_service_provider(self):
        service = GoogleAuthService()
        assert service.provider == SocialProviderChoices.GOOGLE

    def test_google_extract_user_claims(self):
        service = GoogleAuthService()
        payload = {
            "sub": "google-12345",
            "email": "user@gmail.com",
            "given_name": "Alice",
            "family_name": "Wonderland",
            "name": "Alice Wonderland",
            "picture": "https://example.com/alice.jpg",
        }
        uid, email, first, last, extra = service.extract_user_claims(payload)
        assert uid == "google-12345"
        assert email == "user@gmail.com"
        assert first == "Alice"
        assert last == "Wonderland"
        assert extra["picture"] == "https://example.com/alice.jpg"

    @patch("core.apps.users.services.social.google.google_id_token.verify_oauth2_token")
    def test_google_verify_token_success(self, mock_verify):
        mock_verify.return_value = {"sub": "123", "email": "alice@gmail.com"}
        service = GoogleAuthService()
        payload = service.verify_token("valid-token")
        assert payload["sub"] == "123"

    @patch("core.apps.users.services.social.google.google_id_token.verify_oauth2_token")
    def test_google_verify_token_failure(self, mock_verify):
        mock_verify.side_effect = Exception("Signature expired")
        service = GoogleAuthService()
        with pytest.raises(
            ValidationError, match="Invalid Google authentication token"
        ):
            service.verify_token("invalid-token")

    @patch.object(GoogleAuthService, "verify_token")
    @patch.object(SocialAccount.objects, "filter")
    def test_authenticate_or_register_existing_social_account(
        self, mock_filter, mock_verify
    ):
        mock_verify.return_value = {
            "sub": "google-123",
            "email": "alice@gmail.com",
            "given_name": "Alice",
            "family_name": "Wonderland",
        }
        mock_account = MagicMock()
        mock_account.user = User(
            id="123e4567-e89b-12d3-a456-426614174000",
            username="alice",
            email="alice@gmail.com",
        )
        mock_filter.return_value.select_related.return_value.first.return_value = (
            mock_account
        )

        service = GoogleAuthService()
        user, created = service.authenticate_or_register("valid-token")
        assert created is False
        assert user.email == "alice@gmail.com"

    @patch.object(GoogleAuthService, "verify_token")
    @patch.object(SocialAccount.objects, "filter")
    @patch.object(SocialAccount.objects, "create")
    @patch.object(User.objects, "filter")
    def test_authenticate_or_register_existing_user_by_email(
        self, mock_user_filter, mock_sa_create, mock_sa_filter, mock_verify
    ):
        mock_verify.return_value = {
            "sub": "google-123",
            "email": "alice@gmail.com",
            "given_name": "Alice",
            "family_name": "Wonderland",
        }
        mock_sa_filter.return_value.select_related.return_value.first.return_value = (
            None
        )
        existing_user = User(
            id="123e4567-e89b-12d3-a456-426614174000",
            username="alice",
            email="alice@gmail.com",
            is_email_verified=False,
        )
        existing_user.save = MagicMock()
        mock_user_filter.return_value.first.return_value = existing_user

        service = GoogleAuthService()
        user, created = service.authenticate_or_register("valid-token")
        assert created is False
        assert user.is_email_verified is True
        existing_user.save.assert_called_once()
        mock_sa_create.assert_called_once()

    @patch.object(GoogleAuthService, "verify_token")
    @patch.object(SocialAccount.objects, "filter")
    @patch.object(SocialAccount.objects, "create")
    @patch.object(User.objects, "filter")
    @patch.object(User.objects, "create_user")
    def test_authenticate_or_register_new_user(
        self,
        mock_create_user,
        mock_user_filter,
        mock_sa_create,
        mock_sa_filter,
        mock_verify,
    ):
        mock_verify.return_value = {
            "sub": "google-456",
            "email": "bob@gmail.com",
            "given_name": "Bob",
            "family_name": "Builder",
        }
        mock_sa_filter.return_value.select_related.return_value.first.return_value = (
            None
        )
        mock_user_filter.return_value.first.return_value = None

        new_user = User(
            id="223e4567-e89b-12d3-a456-426614174000",
            username="bob",
            email="bob@gmail.com",
            is_email_verified=True,
        )
        mock_create_user.return_value = new_user

        service = GoogleAuthService()
        user, created = service.authenticate_or_register("valid-token")
        assert created is True
        assert user.email == "bob@gmail.com"
        mock_create_user.assert_called_once_with(
            first_name="Bob",
            last_name="Builder",
            email="bob@gmail.com",
            is_email_verified=True,
        )
        mock_sa_create.assert_called_once()


class TestSocialAuthServiceFactory:
    """Tests for SocialAuthServiceFactory."""

    def test_get_service_google(self):
        service = SocialAuthServiceFactory.get_service(SocialProviderChoices.GOOGLE)
        assert isinstance(service, GoogleAuthService)

    def test_get_service_unsupported(self):
        with pytest.raises(ValueError, match="Unsupported social auth provider"):
            SocialAuthServiceFactory.get_service("myspace")

    @patch.object(GoogleAuthService, "authenticate_or_register")
    def test_authenticate_or_register_dispatch(self, mock_auth):
        mock_user = MagicMock()
        mock_auth.return_value = (mock_user, True)
        user, created = SocialAuthServiceFactory.authenticate_or_register(
            SocialProviderChoices.GOOGLE, "valid-token"
        )
        assert created is True
        assert user == mock_user
        mock_auth.assert_called_once_with(token_str="valid-token")


class TestSMSBackends:
    """Tests for SMS backends."""

    def test_console_sms_backend(self):
        backend = ConsoleSMSBackend()
        result = backend.send_sms(to="+1234567890", message="Test code: 123456")
        assert result is True

    def test_base_sms_backend_cannot_instantiate_abstract(self):
        with pytest.raises(TypeError):
            BaseSMSBackend()  # Can't instantiate abstract class with abstract method


class TestOTPLogServiceFunctionality:
    """Tests covering OTPLog creation, audit trail tracking, and verification marking."""

    def setup_method(self):
        cache.clear()

    def teardown_method(self):
        cache.clear()

    @patch("core.apps.users.services.otp.base.queue_task")
    @patch.object(PhoneOTPService, "check_user_exists", return_value=True)
    @patch.object(PhoneOTPService, "deliver", return_value=True)
    def test_send_otp_success_queues_sent_log(
        self, mock_deliver, mock_exists, mock_queue_task
    ):
        service = PhoneOTPService()
        result = service.send_otp(
            identifier="+1555123456", purpose=OTPPurposeChoices.LOGIN
        )

        assert result is True
        mock_exists.assert_called_once_with("+1555123456")
        mock_deliver.assert_called_once()
        mock_queue_task.assert_called_once()
        task_name = mock_queue_task.call_args[0][0]
        task_args = mock_queue_task.call_args[1]["task_args"]
        task_kwargs = mock_queue_task.call_args[1]["task_kwargs"]

        assert task_name == "core.apps.users.tasks.create_otp_log_task"
        assert task_args == ("+1555123456",)
        assert task_kwargs["recipient"] == "+1555123456"
        assert task_kwargs["status"] == OTPDeliveryStatusChoices.SENT.value
        assert task_kwargs["channel"] == OTPChannelChoices.PHONE
        assert task_kwargs["purpose"] == OTPPurposeChoices.LOGIN
        assert "successfully" in task_kwargs["message"]

    @patch("core.apps.users.services.otp.base.queue_task")
    @patch.object(PhoneOTPService, "check_user_exists", return_value=False)
    @patch.object(PhoneOTPService, "deliver")
    def test_send_otp_user_not_found_queues_failed_log(
        self, mock_deliver, mock_exists, mock_queue_task
    ):
        service = PhoneOTPService()
        result = service.send_otp(
            identifier="+1555000000", purpose=OTPPurposeChoices.LOGIN
        )

        assert result is False
        mock_deliver.assert_not_called()
        mock_queue_task.assert_called_once()
        task_kwargs = mock_queue_task.call_args[1]["task_kwargs"]
        assert task_kwargs["status"] == OTPDeliveryStatusChoices.FAILED.value
        assert "No user found" in task_kwargs["message"]
        assert "traceback" in task_kwargs

    @patch("core.apps.users.services.otp.base.queue_task")
    @patch.object(PhoneOTPService, "check_user_exists")
    @patch.object(PhoneOTPService, "deliver", return_value=False)
    def test_send_otp_delivery_failure_queues_failed_log(
        self, mock_deliver, mock_exists, mock_queue_task
    ):
        service = PhoneOTPService()
        result = service.send_otp(
            identifier="+1555123456", purpose=OTPPurposeChoices.SIGNUP
        )

        assert result is False
        mock_exists.assert_not_called()
        mock_queue_task.assert_called_once()
        task_kwargs = mock_queue_task.call_args[1]["task_kwargs"]
        assert task_kwargs["status"] == OTPDeliveryStatusChoices.FAILED.value
        assert "Failed to deliver" in task_kwargs["message"]

    @patch("core.apps.users.services.otp.base.queue_task")
    @patch.object(
        PhoneOTPService, "deliver", side_effect=RuntimeError("SMS Gateway 500")
    )
    def test_send_otp_delivery_exception_queues_failed_log(
        self, mock_deliver, mock_queue_task
    ):
        service = PhoneOTPService()
        result = service.send_otp(
            identifier="+1555123456", purpose=OTPPurposeChoices.SIGNUP
        )

        assert result is False
        mock_queue_task.assert_called_once()
        task_kwargs = mock_queue_task.call_args[1]["task_kwargs"]
        assert task_kwargs["status"] == OTPDeliveryStatusChoices.FAILED.value
        assert "SMS Gateway 500" in task_kwargs["message"]

    @patch.object(OTPLog.objects, "filter")
    def test_mark_otp_log_verified_success(self, mock_filter):
        mock_log = MagicMock()
        mock_log.recipient = "+1555123456"
        mock_log.status = OTPDeliveryStatusChoices.SENT.value
        mock_filter.return_value.order_by.return_value.first.return_value = mock_log

        updated = BaseOTPService._mark_otp_log_verified("+1555123456")

        assert updated is mock_log
        assert mock_log.status == OTPDeliveryStatusChoices.VERIFIED.value
        assert "verified successfully" in mock_log.message
        mock_log.save.assert_called_once()

    @patch.object(OTPLog.objects, "filter")
    def test_mark_otp_log_verified_case_insensitive(self, mock_filter):
        mock_log = MagicMock()
        mock_filter.return_value.order_by.return_value.first.return_value = mock_log

        BaseOTPService._mark_otp_log_verified("Alice@EXAMPLE.com ")

        mock_filter.assert_called_once()
        filter_kwargs = mock_filter.call_args[1]
        assert filter_kwargs["recipient__iexact"] == "Alice@EXAMPLE.com"
        assert filter_kwargs["status"] == OTPDeliveryStatusChoices.SENT.value

    @patch.object(OTPLog.objects, "filter")
    def test_mark_otp_log_verified_not_found(self, mock_filter):
        mock_filter.return_value.order_by.return_value.first.return_value = None

        updated = BaseOTPService._mark_otp_log_verified("+1555999999")

        assert updated is None

    @patch.object(
        OTPLog.objects, "filter", side_effect=Exception("DB connection dropped")
    )
    def test_mark_otp_log_verified_handles_exception_gracefully(self, mock_filter):
        updated = BaseOTPService._mark_otp_log_verified("+1555123456")
        assert updated is None

    @patch.object(OTPLog.objects, "create")
    def test_create_otp_log_task_execution(self, mock_create):
        result = create_otp_log_task(
            identifier="+1555123456",
            recipient="+1555123456",
            channel=OTPChannelChoices.PHONE,
            purpose=OTPPurposeChoices.LOGIN,
            status=OTPDeliveryStatusChoices.SENT.value,
            message="OTP dispatched successfully.",
            traceback="",
        )

        assert "created successfully" in result
        mock_create.assert_called_once_with(
            recipient="+1555123456",
            channel=OTPChannelChoices.PHONE,
            purpose=OTPPurposeChoices.LOGIN,
            status=OTPDeliveryStatusChoices.SENT.value,
            message="OTP dispatched successfully.",
            traceback="",
        )

    @patch.object(OTPLog.objects, "create")
    def test_create_otp_log_task_with_recipient_only(self, mock_create):
        result = create_otp_log_task(
            recipient="test@example.com",
            channel=OTPChannelChoices.EMAIL,
            purpose=OTPPurposeChoices.SIGNUP,
            status=OTPDeliveryStatusChoices.SENT.value,
        )

        assert "created successfully" in result
        mock_create.assert_called_once_with(
            recipient="test@example.com",
            channel=OTPChannelChoices.EMAIL,
            purpose=OTPPurposeChoices.SIGNUP,
            status=OTPDeliveryStatusChoices.SENT.value,
            message="",
            traceback="",
        )

    @patch.object(OTPServiceFactory, "send_otp")
    def test_send_otp_task_execution(self, mock_factory_send):
        mock_factory_send.return_value = True
        result = send_otp_task(
            identifier="+1555123456",
            channel=OTPChannelChoices.PHONE,
            purpose=OTPPurposeChoices.LOGIN,
        )

        assert "sent successfully" in result
        mock_factory_send.assert_called_once_with(
            identifier="+1555123456",
            channel=OTPChannelChoices.PHONE,
            purpose=OTPPurposeChoices.LOGIN,
        )
