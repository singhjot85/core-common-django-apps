from django.conf import settings
from django.db import connection, models
from django.utils.translation import gettext_lazy as _

from core.apps.integrations.constants import (
    CredentialsNameChoices,
    IntegrationKeyChoices,
)
from core.utils.models import BaseModel


def get_credentials_file_path(instance, filename: str) -> str:
    """
    Generate dynamic schema-aware upload path for credentials files.
    """
    name = getattr(instance, "name", "credentials")
    return f"{connection.schema_name}/credentials/{name}_{filename}"


class AbstractCredentialsManager(BaseModel):
    """
    Manages provider credentials, secrets, tokens, or configuration key files.
    """

    CREDENTIAL_FILE_CALLABLE = get_credentials_file_path

    name = models.CharField(
        max_length=64,
        choices=CredentialsNameChoices.choices,
        default=CredentialsNameChoices.CUSTOM,
        verbose_name=_("Provider Name"),
    )
    details = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Credential Details"),
        help_text=_(
            "JSON payload containing API credentials (API key, secret, auth tokens)."
        ),
    )
    file = models.FileField(
        upload_to=CREDENTIAL_FILE_CALLABLE,
        null=True,
        blank=True,
        verbose_name=_("Credential File"),
        help_text=_("Optional key file (e.g. JSON service account, APNs .p8, certs)."),
    )
    expires_on = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Expires On"),
        help_text=_("Optional expiration timestamp for the credential/token."),
    )

    class Meta:
        abstract = True
        verbose_name = _("Credentials Manager")
        verbose_name_plural = _("Credentials Managers")

    def __str__(self) -> str:
        return f"{self.get_name_display()} ({self.pk})"


class AbstractIntegration(BaseModel):
    """
    Core integration entity managing service activation, credentials, and mock routing.
    """

    integration_key = models.CharField(
        max_length=64,
        null=False,
        blank=False,
        choices=IntegrationKeyChoices.choices,
        verbose_name=_("Integration Key"),
    )
    label = models.CharField(
        max_length=128,
        verbose_name=_("Label"),
        help_text=_("User-friendly identifier for this service configuration."),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is Active"),
        help_text=_("Controls whether this integration is active for operations."),
    )
    has_webhooks = models.BooleanField(
        default=False,
        verbose_name=_("Has Webhooks"),
        help_text=_("Indicates whether this service accepts webhook callbacks."),
    )
    credentials = models.ForeignKey(
        settings.INTEGRATIONS_CREDENTIALS_MANAGER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="integrations",
        verbose_name=_("Credentials"),
    )
    mock = models.BooleanField(
        default=False,
        verbose_name=_("Mock Mode"),
        help_text=_(
            "When enabled, requests route to mock services instead of external endpoints."
        ),
    )

    class Meta:
        abstract = True
        verbose_name = _("Integration")
        verbose_name_plural = _("Integrations")

    def __str__(self) -> str:
        return f"{self.label} ({self.get_integration_key_display()})"
