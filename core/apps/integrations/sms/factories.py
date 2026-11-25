"""
Model factories for SMS integrations.
"""

import factory

from core.apps.integrations.sms import (
    get_sms_log_model,
    get_sms_template_model,
)
from core.apps.integrations.sms.constants import (
    SMSLogStatusChoices,
    SMSTemplateInterfaceTypeChoices,
)

SMSLog = get_sms_log_model()
SMSTemplate = get_sms_template_model()


class SMSTemplateFactory(factory.django.DjangoModelFactory):
    """Factory for generating versioned SMSTemplate records."""

    class Meta:
        model = SMSTemplate

    interface_type = SMSTemplateInterfaceTypeChoices.OTP
    template = "Your code is {{ code }}"
    version = "1.0.0"


class SMSLogFactory(factory.django.DjangoModelFactory):
    """Factory for generating SMSLog audit records."""

    class Meta:
        model = SMSLog

    recipient = "+15551234567"
    status = SMSLogStatusChoices.SUCCESS
    backend = "ConsoleSMSBackend"
    message = "Delivered"
