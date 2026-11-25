"""
Model factories for email integrations.
"""

import factory

from core.apps.integrations.email import (
    get_email_log_model,
    get_email_template_model,
)
from core.apps.integrations.email.constants import (
    EmailLogStatusChoices,
    EmailTemplateInterfaceTypeChoices,
)

EmailLog = get_email_log_model()
EmailTemplate = get_email_template_model()


class EmailTemplateFactory(factory.django.DjangoModelFactory):
    """Factory for generating versioned EmailTemplate records."""

    class Meta:
        model = EmailTemplate

    interface_type = EmailTemplateInterfaceTypeChoices.AUTH
    subject = "Welcome {{ name }}"
    template = "Hello {{ name }}."
    html_template = "<p>Hello {{ name }}.</p>"
    version = "1.0.0"


class EmailLogFactory(factory.django.DjangoModelFactory):
    """Factory for generating EmailLog audit records."""

    class Meta:
        model = EmailLog

    recipient = factory.Faker("email")
    subject = "Test Notification"
    status = EmailLogStatusChoices.SUCCESS
    backend = "ConsoleEmailBackend"
    message = "Delivered"
