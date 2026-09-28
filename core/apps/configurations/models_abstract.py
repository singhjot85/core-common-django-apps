from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from core.apps.configurations import get_configuration_model
from core.apps.configurations.constants import InterfaceTypeChoices
from core.utils.models import BaseModel, BaseVersioningModel


class ConfigurationManager(
    models.Manager.from_queryset(queryset_class=models.QuerySet)
):
    """
    Custom manager for configuration model
    """

    def get_latest(
        self, ordering=None, **filters
    ) -> models.QuerySet["AbstractConfiguration"]:
        """
        Get latest configurations based on given parameters
        """
        Configuration = get_configuration_model()

        if not ordering:
            ordering = "interface_type"

        return (
            self.filter(**filters)
            .order_by(*ordering, Configuration.DEFAULT_ORDERING)
            .distinct(*ordering)
        )


class AbstractConfiguration(BaseVersioningModel):
    """
    Configurations model to store database configuration values
    """

    name = models.CharField(max_length=124, null=True, blank=True)
    interface_type = models.CharField(
        null=False, blank=False, choices=InterfaceTypeChoices.choices
    )

    details = models.JSONField(blank=True, default=dict, encoder=DjangoJSONEncoder)
    schema = models.ForeignKey(
        settings.CONFIGURATIONS_CONFIGURATION_SCHEMA_MODEL,
        on_delete=models.PROTECT,
        related_name="configurations",
        null=True,
        blank=True,
    )

    objects: ConfigurationManager = ConfigurationManager()

    class Meta:
        abstract = True
        verbose_name = "Configuration"
        verbose_name_plural = "Configurations"

    def __str__(self):
        return f"{self.name} - {self.version}"


class AbstractConfigurationSchema(BaseModel):
    """
    Configuration schema model to store configuration schema values
    """

    interface_type = models.CharField(
        null=False, blank=False, choices=InterfaceTypeChoices.choices
    )
    schema = models.JSONField(blank=True, default=dict, encoder=DjangoJSONEncoder)

    class Meta:
        abstract = True
        verbose_name = "Configuration Schema"
        verbose_name_plural = "Configuration Schemas"
