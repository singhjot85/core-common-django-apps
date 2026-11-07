"""
Settings definitions for the payments integrations sub-app.
"""

from core.utils.app_settings import BaseSettings
from core.utils.app_settings.types import Settings, SettingsType


class IntegrationsPaymentsSettings(BaseSettings):
    """
    Settings descriptor container for payment processing defaults and gateway drivers.
    """

    SETTINGS_KEY = "CORE_INTEGRATIONS_PAYMENTS_SETTINGS"

    BACKEND = Settings(
        default="core.backends.payment.console.ConsolePaymentBackend",
        data_type=SettingsType.IMPORT.value,
        help_text="Payment processing backend adapter class.",
    )
    DEFAULT_CURRENCY = Settings(
        default="USD",
        data_type=str,
        help_text="Default 3-letter currency code.",
    )
