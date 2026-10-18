from unittest.mock import MagicMock, patch

from django.apps import apps
from django.contrib.auth.models import AbstractUser as DjangoAbstractUser

from core.apps.users import (
    get_otp_log_model,
    get_social_account_model,
    get_system_user,
    get_user_model,
)
from core.apps.users.constants import (
    OTPChannelChoices,
    OTPDeliveryStatusChoices,
    OTPPurposeChoices,
    SocialProviderChoices,
)
from core.apps.users.signals import create_system_user_callback
from core.utils.models import BaseModel, BaseUserModel
from core.utils.models.soft_delete import DeletionTrackingModel

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


class TestSystemUserAndSoftDelete:
    """Tests verifying get_system_user, post_migrate receiver, and soft_delete fallback."""

    @patch.object(User.objects, "filter")
    def test_get_system_user_existing(self, mock_filter):
        mock_user = MagicMock()
        mock_user.username = "system"
        mock_filter.return_value.first.return_value = mock_user

        user = User.get_system_user()
        assert user is mock_user
        mock_filter.assert_called_once_with(username="system")

    @patch.object(User.objects, "filter")
    def test_get_system_user_missing_no_create(self, mock_filter):
        mock_filter.return_value.first.return_value = None

        user = User.get_system_user(create=False)
        assert user is None

    @patch.object(User, "create_system_user")
    @patch.object(User.objects, "filter")
    def test_get_system_user_missing_with_create(self, mock_filter, mock_create):
        mock_filter.return_value.first.return_value = None
        mock_created_user = MagicMock()
        mock_create.return_value = mock_created_user

        user = User.get_system_user(create=True)
        assert user is mock_created_user
        mock_create.assert_called_once()

    @patch.object(User, "get_system_user")
    def test_system_user_alias(self, mock_get_system):
        mock_user = MagicMock()
        mock_get_system.return_value = mock_user

        assert User.system_user() is mock_user
        mock_get_system.assert_called_once()

    @patch.object(User, "get_system_user")
    def test_module_convenience_get_system_user(self, mock_get_system):
        mock_user = MagicMock()
        mock_get_system.return_value = mock_user

        assert get_system_user() is mock_user
        mock_get_system.assert_called_once_with(create=False)

    @patch.object(User.objects, "create")
    @patch.object(User.objects, "all_objects")
    def test_create_system_user_new(self, mock_all_objects, mock_create):
        mock_all_objects.return_value.filter.return_value.first.return_value = None
        mock_instance = MagicMock()
        mock_instance.has_usable_password.return_value = True
        mock_create.return_value = mock_instance

        user = User.create_system_user()
        assert user is mock_instance
        mock_create.assert_called_once_with(
            username="system",
            first_name="System",
            last_name="User",
            is_active=True,
            is_staff=False,
            is_superuser=False,
        )
        mock_instance.set_unusable_password.assert_called_once()
        mock_instance.save.assert_called_once_with(update_fields=["password"])

    @patch.object(User.objects, "all_objects")
    def test_create_system_user_restores_soft_deleted(self, mock_all_objects):
        mock_instance = MagicMock()
        mock_instance.is_removed = True
        mock_instance.has_usable_password.return_value = False
        mock_all_objects.return_value.filter.return_value.first.return_value = (
            mock_instance
        )

        user = User.create_system_user()
        assert user is mock_instance
        assert mock_instance.is_removed is False
        mock_instance.save.assert_called_once_with(update_fields=["is_removed"])

    @patch.object(User, "create_system_user")
    def test_create_system_user_post_migrate_signal(self, mock_create):
        mock_system_user = MagicMock()
        mock_system_user.username = "system"
        mock_create.return_value = mock_system_user

        users_app_config = apps.get_app_config("users")
        result = create_system_user_callback(sender=users_app_config)

        assert result is mock_system_user
        mock_create.assert_called_once()

    @patch.object(User, "create_system_user", side_effect=Exception("DB Error"))
    def test_create_system_user_post_migrate_signal_error_handling(self, mock_create):
        users_app_config = apps.get_app_config("users")
        result = create_system_user_callback(sender=users_app_config)
        assert result is None

    @patch.object(User, "get_system_user")
    def test_soft_delete_fallback_resolves_system_user(self, mock_get_system):
        mock_sys_user = MagicMock(spec=User)
        mock_get_system.return_value = mock_sys_user

        dummy = MagicMock(spec=DeletionTrackingModel)
        dummy.removed_by = None
        fallback_user = DeletionTrackingModel._get_fallback_user(dummy)
        assert fallback_user is mock_sys_user
        mock_get_system.assert_called_once()
