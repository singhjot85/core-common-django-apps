from django.contrib import admin

from core.apps.integrations.payments import get_payment_log_model
from core.utils.admin import private_admin_site

PaymentLog = get_payment_log_model()


@admin.register(PaymentLog, site=private_admin_site)
class PaymentLogAdmin(admin.ModelAdmin):
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
