from core.utils.app_settings import BaseSettings


class IntegrationsSettings(BaseSettings):
    """
    Settings for Integrations framework. The singleton is created in __init__.py, never here.
    """

    SETTINGS_KEY = "CORE_INTEGRATIONS_SETTINGS"
