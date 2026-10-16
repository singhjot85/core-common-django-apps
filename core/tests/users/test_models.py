from django.contrib.auth.models import AbstractUser as DjangoAbstractUser

from core.apps.users import get_otp_log_model, get_social_account_model, get_user_model
from core.apps.users.constants import (
    OTPChannelChoices,
    OTPDeliveryStatusChoices,
    OTPPurposeChoices,
    SocialProviderChoices,
)
from core.utils.models import BaseModel, BaseUserModel

User = get_user_model()
SocialAccount = get_social_account_model()
OTPLog = get_otp_log_model()


class TestUserModelUnits:
    """Unit tests verifying User model architecture and properties without DB."""

    def test_user_model_inheritance(self):
        """User must inherit from Django's AbstractUser and Core's BaseUserModel."""
        assert issubclass(User, DjangoAbstractUser)
        assert issubclass(User, BaseUserModel)
        assert issubclass(User, BaseModel)

    def test_user_id_field_is_uuid(self):
        """User model primary key must be a UUIDField."""
        id_field = User._meta.get_field("id")
        assert id_field.primary_key is True
        assert "UUIDField" in id_field.get_internal_type()

    def test_user_full_name_property(self):
        """full_name must combine first and last name, or fallback to username."""
        user = User(first_name="Jane", last_name="Doe", username="jane_doe")
        assert user.full_name == "Jane Doe"

        user_first_only = User(first_name="Jane", username="jane_doe")
        assert user_first_only.full_name == "Jane"

        user_no_name = User(username="anonymous_coder")
        assert user_no_name.full_name == "anonymous_coder"

    def test_user_has_password_usable_vs_unusable(self):
        """has_password should accurately report whether a usable password exists."""
        user_with_pw = User(username="user1")
        user_with_pw.set_password("SecurePass123!")
        assert user_with_pw.has_password is True
        assert user_with_pw.has_usable_password() is True

        user_unusable_pw = User(username="user2")
        user_unusable_pw.set_unusable_password()
        assert user_unusable_pw.has_password is False
        assert user_unusable_pw.has_usable_password() is False

    def test_user_string_representation(self):
        """__str__ should return username, email, phone, or pk."""
        user = User(
            username="alex99", email="alex@example.com", phone_number="+1234567890"
        )
        assert str(user) == "alex99"

        user_no_uname = User(
            username="", email="alex@example.com", phone_number="+1234567890"
        )
        assert str(user_no_uname) == "alex@example.com"

        user_phone_only = User(username="", email="", phone_number="+1234567890")
        assert str(user_phone_only) == "+1234567890"


class TestSocialAccountModelUnits:
    """Unit tests verifying SocialAccount model."""

    def test_social_account_inheritance(self):
        """SocialAccount must inherit from BaseModel."""
        assert issubclass(SocialAccount, BaseModel)

    def test_social_account_str(self):
        """__str__ must format provider display, uid, and user."""
        user = User(username="john_doe")
        sa = SocialAccount(
            user=user, provider=SocialProviderChoices.GOOGLE, uid="google-sub-123"
        )
        assert "Google" in str(sa)
        assert "google-sub-123" in str(sa)


class TestOTPLogModelUnits:
    """Unit tests verifying OTPLog model."""

    def test_otp_log_inheritance(self):
        """OTPLog must inherit from BaseLogModel."""
        from core.utils.models import BaseLogModel

        assert issubclass(OTPLog, BaseLogModel)

    def test_otp_log_status_choices(self):
        """OTPLog STATUS must use OTPDeliveryStatusChoices."""
        OTPLog._meta.get_field("status")
        choice_keys = [c[0] for c in OTPLog.STATUS]
        assert "pending" in choice_keys
        assert "sent" in choice_keys
        assert "failed" in choice_keys
        assert "verified" in choice_keys
        assert "expired" in choice_keys
        # Ensure 'created' is NOT in choices (preventing StatusModel clash)
        assert "created" not in choice_keys

    def test_otp_log_str(self):
        """__str__ must display recipient, channel, and status."""
        log = OTPLog(
            recipient="+1234567890",
            channel=OTPChannelChoices.PHONE,
            purpose=OTPPurposeChoices.LOGIN,
            status=OTPDeliveryStatusChoices.SENT,
        )
        assert "+1234567890" in str(log)
        assert "phone" in str(log)
        assert "sent" in str(log)
