"""
Abstract base models and upload path generators for integrations and credentials.
"""

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

    Args:
        instance (AbstractCredentialsManager): Instance owning the uploaded credential file.
        filename (str): Base name of the uploaded credential file.

    Returns:
        str: Schema-prefixed storage path for file uploads.
    """
    name = getattr(instance, "name", "credentials")
    return f"{connection.schema_name}/credentials/{name}_{filename}"


class AbstractCredentialsManager(BaseModel):
    """
    Manage provider credentials, secrets, tokens, or configuration key files.

    Provides tenant-scoped credential storage with optional expiration tracking
    and schema-isolated file attachments (such as APNs certificates or service accounts).

    Relations:
        integrations (ReverseForeignKey): Integration records referencing these credentials.

    Attributes:
        name (str): Provider choice name from ``CredentialsNameChoices``.
        details (dict): Structured JSON dictionary containing API secrets and keys.
        file (FieldFile): Optional key or certificate file stored in schema path.
        expires_on (datetime): Optional expiration timestamp for the credential.
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
        """
        Return the display label and primary key for the credentials instance.

        Returns:
            str: Formatted provider name display with primary key.
        """
        return f"{self.get_name_display()} ({self.pk})"


class AbstractIntegration(BaseModel):
    """
    Manage service activation, provider credentials, and mock routing.

    Controls whether specific integration categories (email, SMS, payments)
    are enabled for the current tenant and whether operations should route to mock services.

    Relations:
        credentials (ForeignKey): CredentialsManager instance providing API keys or certs.

    Attributes:
        integration_key (str): Service category choice from ``IntegrationKeyChoices``.
        label (str): Human-friendly name for this integration configuration.
        is_active (bool): Whether the integration is active for live operations.
        has_webhooks (bool): Indicates if the integration handles inbound webhooks.
        mock (bool): When True, bypasses third-party APIs and routes to mock services.
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
        """
        Return the human-readable label and integration category.

        Returns:
            str: Formatted label with category display name.
        """
        return f"{self.label} ({self.get_integration_key_display()})"
