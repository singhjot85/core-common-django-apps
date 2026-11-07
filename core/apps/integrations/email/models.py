"""
Concrete swappable models for email templates and dispatch logs.
"""

from core.apps.integrations.email import models_abstract


class EmailLog(models_abstract.AbstractEmailLog):
    """
    Concrete swappable model representing an email dispatch audit record.
    """

    class Meta(models_abstract.AbstractEmailLog.Meta):
        swappable = "INTEGRATIONS_EMAIL_EMAIL_LOG_MODEL"


class EmailTemplate(models_abstract.AbstractEmailTemplate):
    """
    Concrete swappable model representing a versioned email template.
    """

    class Meta(models_abstract.AbstractEmailTemplate.Meta):
        swappable = "INTEGRATIONS_EMAIL_EMAIL_TEMPLATE_MODEL"
