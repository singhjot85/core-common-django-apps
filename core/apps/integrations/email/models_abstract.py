"""
Abstract base models for versioned email templates and delivery logs.
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.apps.integrations.email.constants import (
    EmailLogStatusChoices,
    EmailTemplateInterfaceTypeChoices,
)
from core.utils.models import BaseLogModel, BaseTemplateModel


class AbstractEmailTemplate(BaseTemplateModel):
    """
    Versioned database template for email communications.

    Stores localized subject line and HTML/plain text template bodies.
    Inherits schema-level caching and versioning via ``BaseTemplateModel``.

    Attributes:
        subject (str): Email subject template string supporting template variables.
        html_template (str): HTML formatted email template body.
    """

    INTERFACE_TYPE = EmailTemplateInterfaceTypeChoices.choices

    subject = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name=_("Subject Template"),
        help_text=_("Email subject line template supporting placeholders."),
    )
    html_template = models.TextField(
        verbose_name=_("HTML Template content"),
        null=True,
        blank=True,
        help_text=_("HTML email template body."),
    )

    class Meta(BaseTemplateModel.Meta):
        abstract = True
        verbose_name = _("Email Template")
        verbose_name_plural = _("Email Templates")

    def __str__(self) -> str:
        """
        Return human-readable interface type, version, and subject.

        Returns:
            str: Formatted string representing template identity.
        """
        return f"{self.interface_type} v{self.version} ({self.subject or 'No subject'})"

    @classmethod
    def serialize_for_cache(cls, obj: "AbstractEmailTemplate | None") -> dict:
        """
        Serialize template content and subject for caching in Redis.

        Args:
            obj (AbstractEmailTemplate | None): Template instance to serialize.

        Returns:
            dict: Serialized dictionary with 'plain_text', 'html_template', and 'subject'.
        """
        if not obj:
            return {}

        return {
            "plain_text": obj.template,
            "html_template": obj.html_template,
            "subject": obj.subject,
        }

    @classmethod
    def get_template_source(cls, interface_type):
        """
        Retrieve cached HTML template content for a given interface type.

        Args:
            interface_type (str): Interface type key identifier.

        Returns:
            str | None: Raw HTML template source string from cache, or None.
        """
        serialized = cls.get_template(interface_type)
        return serialized.get("html_template")


class AbstractEmailLog(BaseLogModel):
    """
    Log of email dispatches tracking delivery status, recipient, and backend used.

    Inherits standard audit timestamps, status tracking, and error messaging from ``BaseLogModel``.

    Relations:
        template (ForeignKey): Optional reference to the EmailTemplate used for rendering.

    Attributes:
        recipient (str): Destination email address.
        subject (str): Final rendered email subject line.
        context (dict): Serialized context dictionary supplied during rendering.
        backend (str): Identifier name of the delivery backend used.
    """

    STATUS = EmailLogStatusChoices.choices

    recipient = models.CharField(
        max_length=255,
        verbose_name=_("Recipient Email"),
        db_index=True,
    )
    subject = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Subject"),
    )
    template = models.ForeignKey(
        settings.INTEGRATIONS_EMAIL_EMAIL_TEMPLATE_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="email_logs",
        verbose_name=_("Template"),
    )
    context = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Context Data"),
    )
    backend = models.CharField(
        max_length=128,
        blank=True,
        default="",
        verbose_name=_("Backend"),
    )

    class Meta(BaseLogModel.Meta):
        abstract = True
        verbose_name = _("Email Log")
        verbose_name_plural = _("Email Logs")

    def __str__(self) -> str:
        """
        Return recipient and delivery status summary.

        Returns:
            str: Formatted string of recipient, status display, and primary key.
        """
        return f"Email to {self.recipient} [{self.get_status_display()}] ({self.pk})"
