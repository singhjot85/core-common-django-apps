from core.apps.integrations.email import models_abstract


class EmailLog(models_abstract.AbstractEmailLog):
    """Concrete EmailLog; no fields here. Add them to AbstractEmailLog."""

    class Meta(models_abstract.AbstractEmailLog.Meta):
        swappable = "INTEGRATIONS_EMAIL_EMAIL_LOG_MODEL"


class EmailTemplate(models_abstract.AbstractEmailTemplate):
    """Concrete EmailTemplate; no fields here. Add them to AbstractEmailTemplate."""

    class Meta(models_abstract.AbstractEmailTemplate.Meta):
        swappable = "INTEGRATIONS_EMAIL_EMAIL_TEMPLATE_MODEL"
