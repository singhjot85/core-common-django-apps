from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.apps.integrations.sms.constants import (
    SMSLogStatusChoices,
    SMSTemplateInterfaceTypeChoices,
)
from core.utils.models import BaseLogModel, BaseTemplateModel


class AbstractSMSTemplate(BaseTemplateModel):
    """
    Versioned database template for SMS messages.
    """

    INTERFACE_TYPE = SMSTemplateInterfaceTypeChoices.choices

    class Meta(BaseTemplateModel.Meta):
        abstract = True
        verbose_name = _("SMS Template")
        verbose_name_plural = _("SMS Templates")

    def __str__(self) -> str:
        return f"{self.interface_type} v{self.version}"

    @classmethod
    def serialize_for_cache(cls, obj: "AbstractSMSTemplate | None") -> dict:
        """
        Serialize template content for caching in Redis.
        """
        if not obj:
            return {}
        return {"template": obj.template}


class AbstractSMSLog(BaseLogModel):
    """
    Log of SMS dispatches tracking delivery status, recipient phone, and backend used.
    """

    STATUS = SMSLogStatusChoices.choices

    recipient = models.CharField(
        max_length=64,
        verbose_name=_("Recipient Phone"),
        db_index=True,
    )
    template = models.ForeignKey(
        settings.INTEGRATIONS_SMS_SMS_TEMPLATE_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sms_logs",
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
        verbose_name = _("SMS Log")
        verbose_name_plural = _("SMS Logs")

    def __str__(self) -> str:
        return f"SMS to {self.recipient} [{self.get_status_display()}] ({self.pk})"
