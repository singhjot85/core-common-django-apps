from core.apps.integrations.sms import models_abstract


class SMSLog(models_abstract.AbstractSMSLog):
    """Concrete SMSLog; no fields here. Add them to AbstractSMSLog."""

    class Meta(models_abstract.AbstractSMSLog.Meta):
        swappable = "INTEGRATIONS_SMS_SMS_LOG_MODEL"


class SMSTemplate(models_abstract.AbstractSMSTemplate):
    """Concrete SMSTemplate; no fields here. Add them to AbstractSMSTemplate."""

    class Meta(models_abstract.AbstractSMSTemplate.Meta):
        swappable = "INTEGRATIONS_SMS_SMS_TEMPLATE_MODEL"
