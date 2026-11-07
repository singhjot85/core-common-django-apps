"""
Concrete swappable models for SMS templates and dispatch logs.
"""

from core.apps.integrations.sms import models_abstract


class SMSLog(models_abstract.AbstractSMSLog):
    """
    Concrete swappable model representing an SMS dispatch audit record.
    """

    class Meta(models_abstract.AbstractSMSLog.Meta):
        swappable = "INTEGRATIONS_SMS_SMS_LOG_MODEL"


class SMSTemplate(models_abstract.AbstractSMSTemplate):
    """
    Concrete swappable model representing a versioned SMS template.
    """

    class Meta(models_abstract.AbstractSMSTemplate.Meta):
        swappable = "INTEGRATIONS_SMS_SMS_TEMPLATE_MODEL"
