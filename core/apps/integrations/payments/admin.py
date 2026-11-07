"""
Admin site registrations for payment transaction logs.
"""

from django.contrib import admin

from core.apps.integrations.payments import get_payment_log_model
from core.utils.admin import private_admin_site

PaymentLog = get_payment_log_model()


@admin.register(PaymentLog, site=private_admin_site)
class PaymentLogAdmin(admin.ModelAdmin):
    """
    Admin configuration for PaymentLog model on the private tenant site.
    """

    list_display = (
        "id",
        "transaction_id",
        "gateway",
        "amount",
        "currency",
        "status",
        "created",
    )
    list_filter = ("gateway", "status", "currency")
    search_fields = ("transaction_id", "source")
