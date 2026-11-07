"""
Settings definitions for the core integrations framework.
"""

from core.utils.app_settings import BaseSettings


class IntegrationsSettings(BaseSettings):
    """
    Settings descriptor container for the integrations framework.

    The shared singleton is instantiated in ``core.apps.integrations.__init__``.
    """

    SETTINGS_KEY = "CORE_INTEGRATIONS_SETTINGS"
