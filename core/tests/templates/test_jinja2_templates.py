import datetime
from decimal import Decimal

import pytest
from django.template import engines
from django.template.loader import render_to_string
from django.test import RequestFactory

from core.utils.jinja2.environment import jinja2_environment
from core.utils.jinja2.filters import format_currency, format_date, format_datetime


class TestJinja2EnvironmentAndFilters:
    def test_environment_initialization(self):
        env = jinja2_environment()
        assert "static" in env.globals
        assert "url" in env.globals
        assert "format_date" in env.globals
        assert "format_datetime" in env.globals
        assert "format_currency" in env.globals
        assert "format_date" in env.filters
        assert "format_datetime" in env.filters
        assert "currency" in env.filters

    def test_format_date_filter(self):
        d = datetime.date(2026, 10, 5)
        assert format_date(d) == "Oct 05, 2026"
        assert format_date(d, fmt="%Y-%m-%d") == "2026-10-05"
        assert format_date(None) == "-"
        assert format_date("") == "-"
        assert format_date("2026-10-05") == "Oct 05, 2026"

    def test_format_datetime_filter(self):
        dt = datetime.datetime(2026, 10, 5, 14, 30)
        assert format_datetime(dt) == "Oct 05, 2026, 02:30 PM"
        assert format_datetime(None) == "-"

    def test_format_currency_filter(self):
        assert format_currency(Decimal("1250.50")) == "$1,250.50"
        assert format_currency(100) == "$100.00"
        assert format_currency(None) == "$0.00"
        assert format_currency(0) == "$0.00"
        assert format_currency(50, symbol="€") == "€50.00"


class TestCoreComponentMacros:
    @pytest.fixture
    def jinja_engine(self):
        for engine in engines.all():
            if engine.__class__.__name__ == "Jinja2":
                return engine
        return engines["jinja2"]

    @pytest.fixture
    def request_context(self):
        factory = RequestFactory()
        request = factory.get("/")
        return {"request": request}

    def test_button_macro_renders_button_and_link(self, jinja_engine, request_context):
        template_str = """
        {% from "core/components/common/buttons.jinja" import button %}
        {{ button(label="Save", variant="primary", size="md") }}
        {{ button(label="Link", href="/profile", variant="outline") }}
        {{ button(label="Disabled", disabled=True) }}
        """
        tmpl = jinja_engine.from_string(template_str)
        rendered = tmpl.render(request_context)

        assert '<button type="button" class="btn btn-primary btn-md"' in rendered
        assert "Save" in rendered
        assert '<a href="/profile" class="btn btn-outline btn-md"' in rendered
        assert "disabled" in rendered

    def test_badge_macro(self, jinja_engine, request_context):
        template_str = """
        {% from "core/components/common/badges.jinja" import badge %}
        {{ badge("Active", variant="success") }}
        {{ badge("Pending", variant="warning") }}
        """
        tmpl = jinja_engine.from_string(template_str)
        rendered = tmpl.render(request_context)

        assert '<span class="badge badge-success"' in rendered
        assert "Active" in rendered
        assert '<span class="badge badge-warning"' in rendered
        assert "Pending" in rendered

    def test_icon_macro(self, jinja_engine, request_context):
        template_str = """
        {% from "core/components/common/icons.jinja" import icon %}
        {{ icon("home", size=24) }}
        {{ icon("check_circle", size=18, fill=True, extra_classes="text-success") }}
        """
        tmpl = jinja_engine.from_string(template_str)
        rendered = tmpl.render(request_context)

        assert 'class="material-symbols-outlined"' in rendered
        assert "font-size: 24px" in rendered
        assert "home" in rendered
        assert "check_circle" in rendered
        assert "text-success" in rendered
        assert "'FILL' 1" in rendered

    def test_card_and_stat_card_macro(self, jinja_engine, request_context):
        template_str = """
        {% from "core/components/common/cards.jinja" import card, stat_card %}
        {{ stat_card("Active Users", 42, "Monthly active") }}
        {% call card(title="Card Title", subtitle="Card Subtitle") %}
          <p>Card body content</p>
        {% endcall %}
        """
        tmpl = jinja_engine.from_string(template_str)
        rendered = tmpl.render(request_context)

        assert "Active Users" in rendered
        assert "42" in rendered
        assert "Monthly active" in rendered
        assert "Card Title" in rendered
        assert "Card Subtitle" in rendered
        assert "<p>Card body content</p>" in rendered

    def test_table_macro(self, jinja_engine, request_context):
        template_str = """
        {% from "core/components/common/tables.jinja" import table %}
        {{ table(headers=["Name", "Email"], rows=[["Alice", "alice@example.com"], ["Bob", "bob@example.com"]]) }}
        """
        tmpl = jinja_engine.from_string(template_str)
        rendered = tmpl.render(request_context)

        assert "<th>Name</th>" in rendered
        assert "<th>Email</th>" in rendered
        assert "<td>Alice</td>" in rendered
        assert "<td>bob@example.com</td>" in rendered

    def test_form_macros(self, jinja_engine, request_context):
        template_str = """
        {% from "core/components/common/forms.jinja" import input, select, textarea, checkbox %}
        {{ input("first_name", label="First Name", value="John", required=True) }}
        {{ select("status", options=[("1", "One"), ("2", "Two")], selected="2", label="Status") }}
        {{ textarea("bio", label="Biography", value="Hello World") }}
        {{ checkbox("agree", label="I agree", checked=True) }}
        """
        tmpl = jinja_engine.from_string(template_str)
        rendered = tmpl.render(request_context)

        assert 'name="first_name"' in rendered
        assert 'value="John"' in rendered
        assert "required" in rendered
        assert 'name="status"' in rendered
        assert 'value="2" selected' in rendered
        assert 'name="bio"' in rendered
        assert "Hello World</textarea>" in rendered
        assert 'name="agree"' in rendered
        assert "checked" in rendered

    def test_alert_and_modal_macros(self, jinja_engine, request_context):
        template_str = """
        {% from "core/components/feedback/alerts.jinja" import alert %}
        {% from "core/components/feedback/modals.jinja" import modal %}
        {{ alert("Operation succeeded", variant="success") }}
        {% call modal("test_modal", title="Test Modal") %}
          <p>Modal body</p>
        {% endcall %}
        """
        tmpl = jinja_engine.from_string(template_str)
        rendered = tmpl.render(request_context)

        assert "alert alert-success" in rendered
        assert "Operation succeeded" in rendered
        assert 'id="test_modal"' in rendered
        assert "Test Modal" in rendered
        assert "<p>Modal body</p>" in rendered

    def test_sidebar_link_macro(self, jinja_engine, request_context):
        template_str = """
        {% from "core/components/common/sidebar.jinja" import sidebar_link, sidebar_divider %}
        {{ sidebar_link("Customers", href="/crm/", icon_name="groups", is_active=True, badge_text="12") }}
        {{ sidebar_divider() }}
        {{ sidebar_link("Settings", href="/settings/", icon_name="settings") }}
        """
        tmpl = jinja_engine.from_string(template_str)
        rendered = tmpl.render(request_context)

        assert 'href="/crm/"' in rendered
        assert 'class="sidebar-link active"' in rendered
        assert "Customers" in rendered
        assert "groups" in rendered
        assert "12" in rendered
        assert 'class="sidebar-divider"' in rendered
        assert 'href="/settings/"' in rendered
        assert "settings" in rendered


class TestFullPageTemplateRendering:
    @pytest.fixture
    def request_obj(self):
        factory = RequestFactory()
        request = factory.get("/")
        return request

    def test_crm_dashboard_template_renders(self, request_obj):
        context = {
            "request": request_obj,
            "PROJECT_LABEL": "Core Apps Test",
            "customers": [
                {
                    "id": "cust-1",
                    "full_name": "Acme Corporation",
                    "customer_type": "ORGANIZATION",
                    "get_customer_type_display": lambda: "Organization",
                    "status": "ACTIVE",
                    "get_status_display": lambda: "Active",
                    "primary_phone": {"phone": "+1 555-0100"},
                    "primary_email": {"email": "contact@acme.com"},
                    "created": datetime.date(2026, 1, 1),
                }
            ],
            "total_customers": 1,
            "active_customers": 1,
            "leads_count": 0,
            "conversion_rate": "100%",
        }
        rendered = render_to_string("crm/crm.jinja", context, request=request_obj)
        assert "Customer Relationship Management" in rendered
        assert "Acme Corporation" in rendered
        assert "+1 555-0100" in rendered
        assert "contact@acme.com" in rendered

    def test_tenants_dashboard_template_renders(self, request_obj):
        context = {
            "request": request_obj,
            "PROJECT_LABEL": "Core Apps Test",
            "tenants": [
                {
                    "id": "tenant-1",
                    "label": "Acme HQ",
                    "schema_name": "acme_hq",
                    "public_id": "Tenant-acme-123",
                    "is_active": True,
                    "created": datetime.date(2026, 1, 1),
                }
            ],
            "total_tenants": 1,
            "active_tenants": 1,
            "total_domains": 1,
        }
        rendered = render_to_string(
            "tenants/tenants.jinja", context, request=request_obj
        )
        assert "Organizations & Tenants" in rendered
        assert "Acme HQ" in rendered
        assert "acme_hq" in rendered
        assert "Tenant-acme-123" in rendered

    def test_sample_project_unified_dashboard_renders(self, request_obj):
        context = {
            "request": request_obj,
            "current_tenant": {
                "label": "Master Corp",
                "schema_name": "master_corp",
                "public_id": "Tenant-master-999",
                "is_active": True,
                "status": "ACTIVE",
                "created": datetime.date(2026, 1, 1),
            },
            "customers": [],
            "active_tenants": 1,
            "total_customers": 0,
            "pending_invoices": 3,
        }
        rendered = render_to_string("dashboard.jinja", context, request=request_obj)
        assert "Enterprise Overview" in rendered
        assert "Master Corp" in rendered
        assert "Pending Invoices" in rendered

    def test_backend_served_ui_view_mock_data(self, request_obj):
        from sample_project.apps.views import BackendServerdUIView

        view = BackendServerdUIView()
        view.request = request_obj
        context = view.get_context_data()

        assert "page_label" in context
        assert "sidebar_links" in context
        assert len(context["sidebar_links"]) == 4
        assert "customers" in context
        assert len(context["customers"]) > 0

        rendered = view.render_to_response(context)
        rendered_content = rendered.rendered_content
        assert "Enterprise Overview" in rendered_content
        assert "Acme Innovations Ltd" in rendered_content
        assert "Enterprise Dashboard" in rendered_content

    def test_base_template_theme_toggle_and_script(self, request_obj):
        context = {"request": request_obj}
        rendered = render_to_string("core/base.jinja", context, request=request_obj)
        assert "data-theme-toggle" in rendered
        assert "core_theme" in rendered
        assert "dark_mode" in rendered
