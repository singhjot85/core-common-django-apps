"""
Settings definitions for the SMS integrations sub-app.
"""

from core.utils.app_settings import BaseSettings
from core.utils.app_settings.types import Settings, SettingsType


class IntegrationsSMSSettings(BaseSettings):
    """
    Settings descriptor container for SMS integration defaults and backend drivers.
    """

    SETTINGS_KEY = "CORE_INTEGRATIONS_SMS_SETTINGS"

    BACKEND = Settings(
        default="core.backends.sms.console.ConsoleSMSBackend",
        data_type=SettingsType.IMPORT.value,
        help_text="SMS delivery backend adapter class.",
    )
