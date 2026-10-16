from core.apps.users import app_settings
from core.apps.users.api.serializers import SignupSerializer, UserDetailsSerializer
from core.utils.backends.sms import ConsoleSMSBackend
from core.utils.generators.username import generate_unique_username
from core.utils.models import BaseUserModel


class TestUsersAppSettings:
    """Tests verifying app_settings configuration and dynamic descriptors."""

    def test_settings_key(self):
        """Settings key should match CORE_USERS_SETTINGS."""
        assert app_settings.SETTINGS_KEY == "CORE_USERS_SETTINGS"

    def test_base_user_model_resolution(self):
        """BASE_USER_MODEL should resolve to core BaseUserModel by default."""
        resolved = app_settings.BASE_USER_MODEL
        assert resolved == BaseUserModel

    def test_serializer_resolutions(self):
        """Serializers should resolve to declared classes."""
        assert app_settings.USER_DETAILS_SERIALIZER == UserDetailsSerializer
        assert app_settings.SIGNUP_SERIALIZER == SignupSerializer

    def test_sms_backend_resolution(self):
        """SMS_BACKEND should resolve to ConsoleSMSBackend by default."""
        assert app_settings.SMS_BACKEND == ConsoleSMSBackend

    def test_username_generator_resolution(self):
        """USERNAME_GENERATOR should resolve to generate_unique_username callable."""
        assert app_settings.USERNAME_GENERATOR == generate_unique_username

    def test_default_descriptor_defaults(self):
        """Check raw default values on descriptors without hitting live cache."""
        from core.apps.users.app_settings import UsersSettings

        assert UsersSettings.ENABLE_PASSWORD_LOGIN.default is True
        assert UsersSettings.ENABLE_OTP_LOGIN.default is True
        assert UsersSettings.ENABLE_SOCIAL_LOGIN.default is True
        assert UsersSettings.ALLOW_AUTO_REGISTRATION_ON_OTP.default is True
        assert UsersSettings.OTP_EXPIRY_SECONDS.default == 300
        assert UsersSettings.OTP_MAX_ATTEMPTS.default == 5
        assert UsersSettings.OTP_LENGTH.default == 6
