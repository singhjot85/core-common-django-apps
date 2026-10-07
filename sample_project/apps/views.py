import json

from django.db import connection
from django.views.generic.base import TemplateView
from rest_framework.renderers import JSONRenderer

from core.apps.tenants import get_tenant_model
from core.apps.tenants.api.serializers import TenantSerializer
from core.utils.checks import is_public


class BackendServerdUIView(TemplateView):
    """
    View to serve UI pages from backend.
    TODO: Database integration in progress. Mocked data provided for initial frontend development.
    """

    template_name = None

    def get_template_names(self):
        """
        Get template name override
        """
        return ["public_dashboard.jinja" if is_public() else "dashboard.jinja"]

    def jsonify(self, data):
        """
        Jsonify the serializers ReturnDict
        """
        return json.loads(JSONRenderer().render(data=data))

    def get_tenant_context(self):
        request_schema = getattr(connection, "schema_name", "public")
        try:
            Tenant = get_tenant_model()
            tenant = Tenant.objects.filter(schema_name=request_schema).first()
            if tenant:
                return self.jsonify(TenantSerializer(tenant).data)
        except Exception:
            pass

        # Fallback / mock tenant context
        primary_domain_str = (
            "public.coreplatform.internal"
            if is_public()
            else "acme.coreplatform.internal"
        )
        return {
            "label": "Master Organization" if is_public() else "Acme Global Corp",
            "schema_name": request_schema,
            "public_id": "TENANT-PUBLIC-001" if is_public() else "TENANT-ACME-001",
            "primary_domain": {
                "domain": primary_domain_str,
                "label": "Primary Domain",
                "is_primary": True,
            },
            "domain": primary_domain_str,
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

        # Financial and operational metrics
        context.setdefault("mrr_amount", "$42.8k")
        context.setdefault("mrr_growth", "+5.8%")
        context.setdefault("draft_invoices", 3)

        # Public platform gauges
        context.setdefault(
            "system_gauges",
            [
                {
                    "label": "Host CPU Cluster",
                    "value": "24%",
                    "status": "Optimal",
                    "percent": 24,
                    "details_left": "8 vCPUs Dedicated",
                    "details_right": "Load Avg: 0.42",
                    "icon": "developer_board",
                    "progress_variant": "secondary",
                },
                {
                    "label": "Allocated Memory",
                    "value": "58%",
                    "status": "Stable",
                    "percent": 58,
                    "details_left": "18.5 GB / 32.0 GB",
                    "details_right": "Swap: 0%",
                    "icon": "memory",
                    "progress_variant": "primary",
                },
                {
                    "label": "NVMe Storage & I/O",
                    "value": "Normal",
                    "status": "420 IOPS",
                    "percent": 32,
                    "details_left": "114.2 GB / 500 GB",
                    "details_right": "Read: 1.2MB/s",
                    "icon": "hard_drive",
                    "progress_variant": "secondary",
                },
            ],
        )

        # Operational Services
        context.setdefault(
            "operational_services",
            [
                {
                    "title": "Redis Cache",
                    "status": "Connected",
                    "status_variant": "success",
                    "icon": "cached",
                    "metrics": [
                        {"label": "Hit Rate", "value": "98.4%"},
                        {
                            "label": "Query Latency",
                            "value": "0.8 ms",
                            "value_classes": "text-success",
                        },
                        {"label": "Memory Footprint", "value": "1.2 GB / 4.0 GB"},
                        {
                            "label": "Tenant Keyspaces",
                            "value": "18 Isolated",
                            "value_classes": "text-primary",
                        },
                    ],
                    "action_label": "Flush Inactive Caches",
                },
                {
                    "title": "Celery Tasks",
                    "status": "0 Queued",
                    "status_variant": "success",
                    "icon": "alt_route",
                    "metrics": [
                        {"label": "Active Workers", "value": "14 Online"},
                        {
                            "label": "Throughput",
                            "value": "248 tasks/min",
                            "value_classes": "text-success",
                        },
                        {"label": "Broker Transport", "value": "RabbitMQ (SSL)"},
                        {"label": "Failed (24h)", "value": "0 (0.0%)"},
                    ],
                    "action_label": "View Task Monitor",
                },
                {
                    "title": "PostgreSQL Pool",
                    "status": "Healthy",
                    "status_variant": "primary",
                    "icon": "database",
                    "metrics": [
                        {"label": "Pool Utilization", "value": "32 / 50 Active"},
                        {
                            "label": "PgBouncer State",
                            "value": "Transaction Mode",
                            "value_classes": "text-success",
                        },
                        {
                            "label": "Replication Lag",
                            "value": "0 ms",
                            "value_classes": "text-success",
                        },
                        {"label": "Cross-Tenant Isolation", "value": "RLS Enforced"},
                    ],
                    "action_label": "Inspect Pool Activity",
                },
            ],
        )

        # Worker Nodes
        context.setdefault(
            "worker_nodes",
            [
                {
                    "node": "celery@worker-node-fra-01",
                    "details": "PID 41924 • Python 3.12",
                    "queues": "default, high-priority",
                    "concurrency": "8 slots",
                    "processed": "42,912 tasks",
                    "status": "Operational",
                    "status_variant": "success",
                },
                {
                    "node": "celery@worker-node-fra-02",
                    "details": "PID 41925 • Python 3.12",
                    "queues": "tenant-invoicing",
                    "concurrency": "4 slots",
                    "processed": "18,304 tasks",
                    "status": "Operational",
                    "status_variant": "success",
                },
                {
                    "node": "celery@worker-node-iad-01",
                    "details": "PID 11082 • Python 3.12",
                    "queues": "async-reports, exports",
                    "concurrency": "8 slots",
                    "processed": "9,820 tasks",
                    "status": "Operational",
                    "status_variant": "success",
                },
                {
                    "node": "celery@worker-node-iad-02",
                    "details": "PID 11094 • Python 3.12",
                    "queues": "periodic-beats",
                    "concurrency": "2 slots",
                    "processed": "81,420 tasks",
                    "status": "Operational",
                    "status_variant": "success",
                },
            ],
        )

        return context


class CoreSampleTemplateView(BackendServerdUIView):
    """
    Sample Template View alias for backward-compatibility.
    """

    template_name = "public_dashboard.jinja" if is_public() else "dashboard.jinja"

    pass
