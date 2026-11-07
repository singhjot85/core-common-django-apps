"""
Concrete swappable models for payment transaction logs.
"""

from core.apps.integrations.payments import models_abstract


class PaymentLog(models_abstract.AbstractPaymentLog):
    """
    Concrete swappable model representing a payment transaction audit record.
    """

    class Meta(models_abstract.AbstractPaymentLog.Meta):
        swappable = "INTEGRATIONS_PAYMENTS_PAYMENT_LOG_MODEL"
