from django.db import connection
from django.views.generic.base import TemplateView

from core.apps.tenants import get_tenant_model
from core.apps.tenants.api.serializers import TenantSerializer
from core.utils.checks import is_public


class BackendServerdUIView(TemplateView):
    """
    View to serve UI pages from backend.
    TODO: Database integration in progress. Mocked data provided for initial frontend development.
    """

    template_name = "public_dashboard.jinja" if is_public() else "dashboard.jinja"

    def get_tenant_context(self):
        request_schema = getattr(connection, "schema_name", "public")
        try:
            Tenant = get_tenant_model()
            tenant = Tenant.objects.filter(schema_name=request_schema).first()
            if tenant:
                return TenantSerializer(tenant).data
        except Exception:
            pass

        # Fallback / mock tenant context
        return {
            "label": "Master Organization" if is_public() else "Acme Global Corp",
            "schema_name": request_schema,
            "public_id": "TENANT-PUBLIC-001" if is_public() else "TENANT-ACME-001",
            "status": "ready",
            "is_active": True,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Page metadata
        context.setdefault("page_label", "Enterprise Dashboard")
        context.setdefault("current_tenant", self.get_tenant_context())
        context.setdefault("active_tenants", 3)
        context.setdefault("total_customers", 8)
        context.setdefault("pending_invoices", 2)
        context.setdefault("unread_notifications_count", 3)

        # Mock dynamic sidebar links
        context.setdefault(
            "sidebar_links",
            [
                {"title": "Home", "href": "/", "icon": "home", "is_active": True},
                {"title": "Customers", "href": "/crm/", "icon": "groups", "badge": "8"},
                {
                    "title": "Organizations",
                    "href": "/tenants/",
                    "icon": "domain",
                    "badge": "3",
                },
                {
                    "title": "Invoices",
                    "href": "/invoices/",
                    "icon": "receipt_long",
                    "badge": "2",
                },
            ],
        )

        # Mock user profile
        context.setdefault(
            "user_profile",
            {
                "name": "Gurjot Singh",
                "email": "gurjot@example.com",
            },
        )

        # Mock customers list
        context.setdefault(
            "customers",
            [
                {
                    "id": "CUST-001",
                    "full_name": "Acme Innovations Ltd",
                    "customer_type": "ORGANIZATION",
                    "get_customer_type_display": lambda: "Organization",
                    "status": "ACTIVE",
                    "get_status_display": lambda: "Active",
                    "primary_phone": {"phone": "+1 555-0199"},
                    "primary_email": {"email": "ops@acme.example"},
                    "created": "2026-03-15",
                },
                {
                    "id": "CUST-002",
                    "full_name": "Jane Doe",
                    "customer_type": "INDIVIDUAL",
                    "get_customer_type_display": lambda: "Individual",
                    "status": "LEAD",
                    "get_status_display": lambda: "Lead",
                    "primary_phone": {"phone": "+1 555-0142"},
                    "primary_email": {"email": "jane.doe@example.com"},
                    "created": "2026-09-20",
                },
                {
                    "id": "CUST-003",
                    "full_name": "Apex Cloud Systems",
                    "customer_type": "ORGANIZATION",
                    "get_customer_type_display": lambda: "Organization",
                    "status": "ACTIVE",
                    "get_status_display": lambda: "Active",
                    "primary_phone": {"phone": "+1 555-0188"},
                    "primary_email": {"email": "billing@apex.example"},
                    "created": "2026-10-01",
                },
            ],
        )

        return context


class CoreSampleTemplateView(BackendServerdUIView):
    """
    Sample Template View alias for backward-compatibility.
    """

    pass
