from core.apps.integrations.payments import models_abstract


class PaymentLog(models_abstract.AbstractPaymentLog):
    """Concrete PaymentLog; no fields here. Add them to AbstractPaymentLog."""

    class Meta(models_abstract.AbstractPaymentLog.Meta):
        swappable = "INTEGRATIONS_PAYMENTS_PAYMENT_LOG_MODEL"
