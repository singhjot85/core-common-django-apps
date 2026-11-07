"""
Settings definitions for the email integrations sub-app.
"""

from core.utils.app_settings import BaseSettings
from core.utils.app_settings.types import Settings, SettingsType


class IntegrationsEmailSettings(BaseSettings):
    """
    Settings descriptor container for email integration defaults and backend drivers.
    """

    SETTINGS_KEY = "CORE_INTEGRATIONS_EMAIL_SETTINGS"

    BACKEND = Settings(
        default="core.backends.email.console.CoreConsoleEmailBackend",
        data_type=SettingsType.IMPORT.value,
        help_text="Email delivery backend adapter class.",
    )
    DEFAULT_FROM_EMAIL = Settings(
        default="noreply@example.com",
        data_type=str,
        help_text="Default sender email address.",
    )
