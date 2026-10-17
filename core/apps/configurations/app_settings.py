from core.utils.app_settings import BaseSettings
from core.utils.app_settings.types import Settings


class ConfigurationsSettings(BaseSettings):
    """
    App settings and runtime configuration for Configurations application.
    """

    SETTINGS_KEY = "CORE_CONFIGURATIONS_SETTINGS"

    DEV_SEEDER_SETUP_PATH = Settings(
        default="setup",
        data_type=str,
        help_text="Path to development seeders directory (relative to CORE_BASE_DIR or absolute path).",
    )
