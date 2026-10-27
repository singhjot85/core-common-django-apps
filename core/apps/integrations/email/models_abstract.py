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
        return f"{self.interface_type} v{self.version} ({self.subject or 'No subject'})"

    @classmethod
    def serialize_for_cache(cls, obj: "AbstractEmailTemplate | None") -> dict:
        """
        Serialize template content and subject for caching in Redis.
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
        """ """
        serialized = cls.get_template(interface_type)
        return serialized.get("html_template")


class AbstractEmailLog(BaseLogModel):
    """
    Log of email dispatches tracking delivery status, recipient, and backend used.
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
        return f"Email to {self.recipient} [{self.get_status_display()}] ({self.pk})"
