from django.views.generic.base import TemplateView


class CoreSampleTemplateView(TemplateView):
    """
    Sample Template View to check out core Jinja2 templates, widgets, and components.
    """

    template_name = "dashboard.jinja"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Sample / mock data so the template renders fully even without pre-seeded DB
        context.setdefault("active_tenants", 3)
        context.setdefault("total_customers", 12)
        context.setdefault("pending_invoices", 4)
        context.setdefault(
            "current_tenant",
            {
                "label": "Acme Global Corp",
                "schema_name": "acme",
                "public_id": "TENANT-ACME-001",
                "status": "ready",
                "is_active": True,
            },
        )
        context.setdefault(
            "customers",
            [
                {
                    "full_name": "Jane Doe",
                    "business_name": "Doe Enterprises",
                    "customer_type": "b2b",
                    "status": "active",
                    "created": "2026-10-01",
                },
                {
                    "full_name": "John Smith",
                    "business_name": "Smith & Co",
                    "customer_type": "individual",
                    "status": "active",
                    "created": "2026-10-02",
                },
                {
                    "full_name": "Alice Johnson",
                    "business_name": "Apex Innovations",
                    "customer_type": "b2b",
                    "status": "lead",
                    "created": "2026-10-04",
                },
            ],
        )
        return context
