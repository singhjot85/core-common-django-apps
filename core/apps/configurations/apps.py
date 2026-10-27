from django.apps import AppConfig


class ConfigurationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core.apps.configurations"
    label = "configurations"

    def ready(self):
        from core.apps.configurations.constants import (  # noqa: PLC0415
            DefaultConfigurationInterfaceTypeChoices,
            InterfaceTypeChoices,
        )

        InterfaceTypeChoices.contribute(DefaultConfigurationInterfaceTypeChoices)
