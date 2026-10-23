import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from django.template import TemplateDoesNotExist, engines
from django.template.loader import get_template, render_to_string
from django.test import RequestFactory
from jinja2 import DictLoader, TemplateNotFound
from jinja2.exceptions import SecurityError

from core.utils.jinja2.environment import (
    jinja2_environment,
    jinja2_sandboxed_environment,
)
from core.utils.jinja2.filters import format_currency, format_date, format_datetime
from core.utils.jinja2.loaders import SafeDatabaseLoader
from sample_project.apps.views import BackendServerdUIView


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
        {{ button(label="Modal", attrs={"data-modal-target": "test_modal"}) }}
        """
        tmpl = jinja_engine.from_string(template_str)
        rendered = tmpl.render(request_context)

        assert 'class="btn btn-primary btn-md"' in rendered
        assert "Save" in rendered
        assert 'href="/profile"' in rendered
        assert 'class="btn btn-outline btn-md"' in rendered
        assert "disabled" in rendered
        assert 'data-modal-target="test_modal"' in rendered
        assert "attrs=" not in rendered

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

        # Subtitle without title should still render header
        sub_tmpl = jinja_engine.from_string("""
        {% from "core/components/common/cards.jinja" import card %}
        {% call card(subtitle="Standalone Subtitle") %}<p>Body</p>{% endcall %}
        """)
        sub_rendered = sub_tmpl.render(request_context)
        assert '<div class="card-header">' in sub_rendered
        assert "Standalone Subtitle" in sub_rendered

    def test_gauge_and_service_card_and_banner_macros(
        self, jinja_engine, request_context
    ):
        template_str = """
        {% from "core/components/common/cards.jinja" import gauge_card, service_card, status_banner, telemetry_strip %}
        {{ gauge_card("Host CPU", "24%", status="Optimal", percent=24, details_left="8 vCPUs", details_right="Load Avg: 0.42") }}
        {{ service_card("Redis Cache", status="Connected", metrics=[{"label": "Hit Rate", "value": "98.4%"}], action_label="Flush Cache") }}
        {% call status_banner(title="All Systems Operational", badge_text="100% SLA") %}
            <button type="button">Sync</button>
        {% endcall %}
        {{ telemetry_strip(title="Search Path: acme", subtitle="Isolation Hash: 0x123", status_badge="READY") }}
        """
        tmpl = jinja_engine.from_string(template_str)
        rendered = tmpl.render(request_context)

        assert "Host CPU" in rendered
        assert "24%" in rendered
        assert "8 vCPUs" in rendered
        assert "Redis Cache" in rendered
        assert "Hit Rate" in rendered
        assert "98.4%" in rendered
        assert "All Systems Operational" in rendered
        assert "100% SLA" in rendered
        assert "Search Path: acme" in rendered
        assert "READY" in rendered

    def test_table_macro(self, jinja_engine, request_context):
        template_str = """
        {% from "core/components/common/tables.jinja" import table %}
        {{ table(headers=["Name", "Email"], rows=[["<script>alert(1)</script>", "bob@example.com"]]) }}
        """
        tmpl = jinja_engine.from_string(template_str)
        rendered = tmpl.render(request_context)

        assert "<th>Name</th>" in rendered
        assert "<th>Email</th>" in rendered
        assert "&lt;script&gt;alert(1)&lt;/script&gt;" in rendered
        assert "<script>" not in rendered
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
        {% call modal("test_modal", title="Test Modal", max_width="650px") %}
          <p>Modal body</p>
        {% endcall %}
        {% call modal("headless_modal") %}
          <p>Headless body</p>
        {% endcall %}
        """
        tmpl = jinja_engine.from_string(template_str)
        rendered = tmpl.render(request_context)

        assert "alert alert-success" in rendered
        assert "Operation succeeded" in rendered
        assert 'id="test_modal"' in rendered
        assert "Test Modal" in rendered
        assert 'aria-labelledby="test_modal_title"' in rendered
        assert 'style="max-width: 650px;"' in rendered
        assert "<p>Modal body</p>" in rendered

        assert 'id="headless_modal"' in rendered
        assert 'aria-labelledby="headless_modal_title"' not in rendered

    def test_message_list_macro(self, jinja_engine, request_context):
        class DummyMsg:
            def __init__(self, message, tags):
                self.message = message
                self.tags = tags

        template_str = """
        {% from "core/components/feedback/alerts.jinja" import message_list %}
        {{ message_list(messages) }}
        """
        tmpl = jinja_engine.from_string(template_str)
        messages = [
            DummyMsg("Operation failed", "error"),
            DummyMsg("Saved successfully", "success"),
            "Simple string alert",
        ]
        rendered = tmpl.render(
            {"request": request_context["request"], "messages": messages}
        )
        assert "alert alert-danger" in rendered
        assert "Operation failed" in rendered
        assert "alert alert-success" in rendered
        assert "Saved successfully" in rendered
        assert "alert alert-info" in rendered
        assert "Simple string alert" in rendered

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
        view = BackendServerdUIView()
        view.request = request_obj
        context = view.get_context_data()

        assert "page_label" in context
        assert "sidebar_links" in context
        assert len(context["sidebar_links"]) == 4
        assert "customers" in context
        assert len(context["customers"]) > 0
        assert "system_gauges" in context
        assert "operational_services" in context
        assert "worker_nodes" in context

        # Public Dashboard rendering
        rendered_public = view.render_to_response(context).rendered_content
        assert "All Systems Operational" in rendered_public
        assert "System Resource Utilization" in rendered_public
        assert "Public Platform Worker Pool" in rendered_public

        # Tenant Dashboard rendering
        rendered_tenant = render_to_string(
            "dashboard.jinja", context, request=request_obj
        )
        assert "Enterprise Overview" in rendered_tenant
        assert "Acme Innovations Ltd" in rendered_tenant
        assert "Recent Customers" in rendered_tenant

    def test_base_template_theme_toggle_and_script(self, request_obj):
        context = {"request": request_obj}
        rendered = render_to_string("core/base.jinja", context, request=request_obj)
        assert "data-theme-toggle" in rendered
        assert "core_theme" in rendered
        assert "dark_mode" in rendered
        assert "tenant-ref-id" not in rendered
        assert "Guest" in rendered
        assert "Admin User" not in rendered
        assert "admin@example.com" not in rendered

    def test_authenticated_view_renders(self, request_obj):
        context = {
            "request": request_obj,
            "PROJECT_LABEL": "Test Core Platform",
            "signin_action": "/login/",
            "signup_action": "/signup/",
            "otp_action": "/otp/",
        }
        rendered = render_to_string(
            "core/views/authenticated_view.jinja", context, request=request_obj
        )
        assert "Test Core Platform" in rendered
        assert "Sign In" in rendered
        assert "Create Account" in rendered
        assert "data-auth-tab" in rendered
        assert "data-auth-method" in rendered
        assert "data-password-toggle" in rendered
        assert "data-otp-box" in rendered
        assert "Create Account" in rendered
        assert "session_timeout_overlay" in rendered
        assert "Session Expired" in rendered

    def test_username_login_template_renders(self):
        factory = RequestFactory()
        request_obj = factory.get("/login/")
        rendered = render_to_string(
            "core/views/auth/username_login.jinja",
            {"request": request_obj, "login_action": "/api/users/v1/auth/login/"},
            request=request_obj,
        )
        assert "data-username-tab" in rendered
        assert "username_login_attempts_warning" in rendered
        assert "btn_username_submit" in rendered
        assert 'name="username"' in rendered
        assert 'name="password"' in rendered
        assert "Sign In" in rendered
        assert "Email" in rendered

    def test_username_login_template_backend_labels_override(self):
        factory = RequestFactory()
        request_obj = factory.get("/login/")
        rendered = render_to_string(
            "core/views/auth/username_login.jinja",
            {
                "request": request_obj,
                "login_action": "/api/users/v1/auth/login/",
                "labels": {
                    "email": "Corporate ID",
                    "sign_in": "Authenticate Now",
                },
            },
            request=request_obj,
        )
        assert "Corporate ID" in rendered
        assert "Authenticate Now" in rendered
        # Password still falls back to default i18n label
        assert "Password" in rendered
        assert 'name="first_name"' in rendered
        assert 'name="last_name"' in rendered

    def test_otp_login_template_renders(self):
        factory = RequestFactory()
        request_obj = factory.get("/login/")
        rendered = render_to_string(
            "core/views/auth/otp_login.jinja",
            {
                "request": request_obj,
                "otp_verify_action": "/api/users/v1/auth/otp/verify/",
            },
            request=request_obj,
        )
        assert "data-otp-tab" in rendered
        assert "btn_send_login_otp" in rendered
        assert "data-otp-box" in rendered
        assert "btn_otp_submit" in rendered
        assert "otp_login_attempts_warning" in rendered
        assert "Phone" in rendered

    def test_core_login_template_renders(self):
        factory = RequestFactory()
        request_obj = factory.get("/login/")
        rendered = render_to_string(
            "core/views/core_login_template.jinja",
            {"request": request_obj, "PROJECT_LABEL": "ACME Core"},
            request=request_obj,
        )
        assert "ACME Core" in rendered
        assert 'data-auth-method="username"' in rendered
        assert 'data-auth-method="otp"' in rendered
        assert "Privacy Policy" in rendered
        assert "Terms" in rendered
        assert "Platform Status" in rendered
        assert "auth_toast_container" in rendered


class TestCoreFormTemplates:
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

    def test_base_form_macro(self, jinja_engine, request_context):
        template_str = """
        {% from "core/forms/base_form.jinja" import base_form %}
        {% call base_form(action="/submit/", method="post", title="User Form", form_errors=["Invalid input"]) %}
            <input type="text" name="sample">
        {% endcall %}
        """
        tmpl = jinja_engine.from_string(template_str)
        rendered = tmpl.render(request_context)

        assert 'action="/submit/"' in rendered
        assert 'method="post"' in rendered
        assert "User Form" in rendered
        assert "Invalid input" in rendered
        assert 'name="sample"' in rendered

    def test_individual_form_field_macros(self, jinja_engine, request_context):
        template_str = """
        {% from "core/forms/form_field_text.jinja" import form_field_text %}
        {% from "core/forms/form_field_email.jinja" import form_field_email %}
        {% from "core/forms/form_field_password.jinja" import form_field_password %}
        {% from "core/forms/form_field_otp.jinja" import form_field_otp %}
        {% from "core/forms/form_field_checkbox.jinja" import form_field_checkbox %}
        {% from "core/forms/form_field_select.jinja" import form_field_select %}
        {% from "core/forms/form_field_hidden.jinja" import form_field_hidden %}

        {{ form_field_text("username", label="Username", value="alice", required=True) }}
        {{ form_field_email("user_email", label="Email") }}
        {{ form_field_password("user_pass", label="Password") }}
        {{ form_field_otp("user_otp", label="Verification Code", digits=6) }}
        {{ form_field_checkbox("remember", label="Remember Me", checked=True) }}
        {{ form_field_select("role", options=[("admin", "Admin"), ("member", "Member")], selected="admin") }}
        {{ form_field_hidden("csrf_dummy", value="dummy_token") }}
        """
        tmpl = jinja_engine.from_string(template_str)
        rendered = tmpl.render(request_context)

        assert 'name="username"' in rendered
        assert 'value="alice"' in rendered
        assert 'name="user_email"' in rendered
        assert 'type="email"' in rendered
        assert 'name="user_pass"' in rendered
        assert 'data-password-toggle="id_user_pass"' in rendered
        assert "data-otp-box" in rendered
        assert 'name="user_otp_0"' in rendered
        assert 'name="user_otp_5"' in rendered
        assert 'name="remember"' in rendered
        assert "checked" in rendered
        assert 'name="role"' in rendered
        assert 'value="admin" selected' in rendered
        assert 'name="csrf_dummy"' in rendered
        assert 'value="dummy_token"' in rendered

    def test_dynamic_form_macro(self, jinja_engine, request_context):
        template_str = """
        {% from "core/forms/dynamic_form.jinja" import dynamic_form %}
        {{ dynamic_form(fields=[
            {"type": "text", "name": "first_name", "label": "First Name", "value": "John"},
            {"type": "email", "name": "work_email", "label": "Work Email"},
            {"type": "password", "name": "account_pass", "label": "Password"},
            {"type": "checkbox", "name": "terms", "label": "I accept"},
            {"type": "select", "name": "tier", "label": "Tier", "options": ["Free", "Pro"], "selected": "Pro"},
            {"type": "hidden", "name": "step", "value": "1"}
        ], action="/api/register/", submit_label="Create Account") }}
        """
        tmpl = jinja_engine.from_string(template_str)
        rendered = tmpl.render(request_context)

        assert 'action="/api/register/"' in rendered
        assert "Create Account" in rendered
        assert 'name="first_name"' in rendered
        assert 'value="John"' in rendered
        assert 'name="work_email"' in rendered
        assert 'name="account_pass"' in rendered
        assert 'data-password-toggle="id_account_pass"' in rendered
        assert 'name="terms"' in rendered
        assert 'name="tier"' in rendered
        assert 'value="Pro" selected' in rendered
        assert 'name="step"' in rendered
        assert 'value="1"' in rendered


class TestSafeDatabaseLoaderAndSandboxedEnvironment:
    def test_safe_database_loader_delegates_to_fallback(self):
        fallback = DictLoader({"test.jinja": "Hello {{ name }}"})
        loader = SafeDatabaseLoader(fallback_loader=fallback)

        source, filename, uptodate = loader.get_source(None, "test.jinja")
        assert source == "Hello {{ name }}"
        assert filename is None
        assert uptodate() is True

    def test_safe_database_loader_resolves_db_template(self):
        loader = SafeDatabaseLoader()
        mock_model = MagicMock()
        mock_model.get_template_source.return_value = "<h1>Hello from DB</h1>"
        mock_model.get_cache_key.return_value = (
            "public:invoices:invoicetemplate:standard"
        )

        with patch.object(loader, "get_template_model", return_value=mock_model):
            source, filename, uptodate = loader.get_source(
                None, "invoices:invoicetemplate:standard"
            )
            assert source == "<h1>Hello from DB</h1>"
            assert filename == "db://invoices/invoicetemplate/standard"
            assert callable(uptodate)

    def test_safe_database_loader_raises_template_not_found(self):
        loader = SafeDatabaseLoader()
        with pytest.raises(TemplateNotFound):
            loader.get_source(None, "nonexistent_file.jinja")

    def test_sandboxed_environment_security(self):
        env = jinja2_sandboxed_environment()
        tmpl = env.from_string("Hello {{ name }}")
        assert tmpl.render({"name": "Alice"}) == "Hello Alice"

        # Verify sandbox prevents access to dangerous internal attributes
        with pytest.raises(SecurityError):
            env.from_string("{{ ''.__class__.__mro__[1].__subclasses__() }}").render()

    def test_jinja2_backend_ignores_non_jinja_extension(self):
        """Verify Jinja2Backend raises TemplateDoesNotExist for non-jinja files (e.g. admin/login.html)."""
        jinja_backend = engines["jinja2"]
        with pytest.raises(TemplateDoesNotExist):
            jinja_backend.get_template("admin/login.html")

    def test_admin_login_resolves_via_dtl(self):
        """Verify admin/login.html resolves successfully using the DjangoTemplates engine."""
        template = get_template("admin/login.html")
        assert template is not None
        assert template.backend.name == "django"
