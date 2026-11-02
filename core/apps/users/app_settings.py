import typing

from core.utils.app_settings import BaseSettings
from core.utils.app_settings.types import Constance, Settings, SettingsType

if typing.TYPE_CHECKING:
    from core.apps.users.api.serializers import SignupSerializer, UserDetailsSerializer
    from core.utils.backends.sms.console import ConsoleSMSBackend
    from core.utils.models import BaseUserModel


class UsersSettings(BaseSettings):
    """
    App settings and runtime configuration for Users application.
    """

    SETTINGS_KEY = "CORE_USERS_SETTINGS"

    # Base Model Swappability (swappable without replacing concrete User)
    BASE_USER_MODEL: type["BaseUserModel"] = Settings(
        default="core.utils.models.BaseUserModel",
        data_type=SettingsType.DEFFERED_IMPORT.value,
        help_text="Base user model from which AbstractUser inherits.",
    )
    AUTO_CREATE_CUSTOMER = Settings(
        default=True,
        data_type=bool,
        help_text="Auto Create a Customer along with user signup.",
    )

    # Serializer Bindings
    USER_DETAILS_SERIALIZER: type["UserDetailsSerializer"] = Settings(
        default="core.apps.users.api.serializers.UserDetailsSerializer",
        data_type=SettingsType.IMPORT.value,
        help_text="Serializer class for serializing authenticated user details.",
    )
    SIGNUP_SERIALIZER: type["SignupSerializer"] = Settings(
        default="core.apps.users.api.serializers.SignupSerializer",
        data_type=SettingsType.IMPORT.value,
        help_text="Serializer class for user signup / registration.",
    )

    # Services & Strategies
    SMS_BACKEND: type["ConsoleSMSBackend"] = Settings(
        default="core.utils.backends.sms.console.ConsoleSMSBackend",
        data_type=SettingsType.IMPORT.value,
        help_text="SMS delivery adapter backend for OTP dispatch.",
    )
    USERNAME_GENERATOR = Settings(
        default="core.utils.generators.username.generate_unique_username",
        data_type=SettingsType.IMPORT.value,
        help_text="Callable to generate unique usernames when omitted during signup.",
    )

    # Runtime Feature Toggles (Constance)
    ENABLE_PASSWORD_LOGIN = Constance(
        default=True,
        help_text="Enable username/password login endpoint.",
        data_type=bool,
    )
    ENABLE_OTP_LOGIN = Constance(
        default=True,
        help_text="Enable phone and email OTP login flows.",
        data_type=bool,
    )
    ENABLE_SOCIAL_LOGIN = Constance(
        default=True,
        help_text="Enable Google and other social logins.",
        data_type=bool,
    )
    ALLOW_AUTO_REGISTRATION_ON_OTP = Constance(
        default=True,
        help_text="Automatically create accounts for unknown numbers on OTP verify.",
        data_type=bool,
    )
    OTP_EXPIRY_SECONDS = Constance(
        default=300,
        help_text="Time-to-live (in seconds) for OTP codes in cache.",
        data_type=int,
    )
    OTP_MAX_ATTEMPTS = Constance(
        default=5,
        help_text="Maximum failed verification attempts allowed per OTP session.",
        data_type=int,
    )

    # Settings
    OTP_LENGTH = Settings(
        default=6,
        data_type=int,
        help_text="Number of digits for generated numeric OTP codes.",
    )
    SYSTEM_USER_USERNAME = Settings(
        default="system",
        data_type=str,
        help_text="Username for the internal system user used for auditing and system operations.",
    )
    LOCKOUT_TOKEN_TIMEOUT = Settings(
        default=86400,  # 24 hours
        data_type=int,
        help_text="Validity for lockout token timeout.",
    )
    ONLY_ALLOW_IN_APP_REDIRECTS = Settings(
        default=True,
        data_type=bool,
        help_text="Enforce that post-authentication redirects only target in-app endpoints.",
    )
