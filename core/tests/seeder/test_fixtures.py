import json
import pathlib

import pytest
from django.conf import settings

from core.apps.configurations.fixtures.seeders import ConfigurationSeeder
from core.apps.crm.fixtures.seeder import CustomerPreferenceTypeSeeder

APPS_DIR = pathlib.Path(__file__).resolve().parents[2] / "apps"
SETUP_DIR = pathlib.Path(__file__).resolve().parents[2] / "setup"


class TestFixtureJSONFiles:
    """Validate that all production fixture JSON files exist and are valid JSON."""

    FIXTURE_PATHS = [
        APPS_DIR
        / "crm"
        / "fixtures"
        / "customer_preference_type"
        / "preference_types.json",
        APPS_DIR
        / "configurations"
        / "fixtures"
        / "configuration"
        / "ui_configuration.json",
        APPS_DIR
        / "configurations"
        / "fixtures"
        / "configuration"
        / "users_template_label.json",
        APPS_DIR
        / "configurations"
        / "fixtures"
        / "configuration_schema"
        / "schemas.json",
        APPS_DIR
        / "configurations"
        / "fixtures"
        / "tenant_configuration"
        / "tenant_configs.json",
        APPS_DIR
        / "tenants"
        / "fixtures"
        / "tenant_configuration"
        / "tenant_config.json",
    ]

    @pytest.mark.parametrize("fixture_path", FIXTURE_PATHS, ids=lambda p: p.name)
    def test_fixture_json_exists(self, fixture_path):
        """Each fixture JSON file must exist."""
        assert fixture_path.exists(), f"Missing fixture: {fixture_path}"

    @pytest.mark.parametrize("fixture_path", FIXTURE_PATHS, ids=lambda p: p.name)
    def test_fixture_json_is_valid(self, fixture_path):
        """Each fixture JSON file must be parseable and contain a list or non-empty dict."""
        if not fixture_path.exists():
            pytest.skip(f"File missing: {fixture_path}")

        data = json.loads(fixture_path.read_text())
        assert isinstance(data, (list, dict)), (
            f"{fixture_path.name} should contain a JSON array or object"
        )
        assert len(data) > 0, f"{fixture_path.name} should not be empty"

    def test_preference_types_have_required_fields(self):
        """CustomerPreferenceType fixture entries must have code, label, data_type."""
        path = (
            APPS_DIR
            / "crm"
            / "fixtures"
            / "customer_preference_type"
            / "preference_types.json"
        )
        data = json.loads(path.read_text())
        for entry in data:
            assert "code" in entry, f"Missing 'code' in {entry}"
            assert "label" in entry, f"Missing 'label' in {entry}"
            assert "data_type" in entry, f"Missing 'data_type' in {entry}"

    @pytest.mark.parametrize(
        "filename", ["ui_configuration.json", "users_template_label.json"]
    )
    def test_configuration_entries_have_required_fields(self, filename):
        """Configuration fixture entries must have name, interface_type, details."""
        path = APPS_DIR / "configurations" / "fixtures" / "configuration" / filename
        data = json.loads(path.read_text())
        entries = data if isinstance(data, list) else [data]
        for entry in entries:
            assert "name" in entry
            assert "interface_type" in entry
            assert "details" in entry

    def test_schema_entries_have_required_fields(self):
        """ConfigurationSchema fixture entries must have interface_type, schema."""
        path = (
            APPS_DIR
            / "configurations"
            / "fixtures"
            / "configuration_schema"
            / "schemas.json"
        )
        data = json.loads(path.read_text())
        for entry in data:
            assert "interface_type" in entry
            assert "schema" in entry
            assert isinstance(entry["schema"], dict)

    PUBLIC_FIXTURE_PATHS = [
        APPS_DIR
        / "configurations"
        / "fixtures"
        / "configuration_schema"
        / "schemas.json",
        APPS_DIR
        / "configurations"
        / "fixtures"
        / "tenant_configuration"
        / "tenant_configs.json",
        APPS_DIR
        / "tenants"
        / "fixtures"
        / "tenant_configuration"
        / "tenant_config.json",
    ]

    @pytest.mark.parametrize("fixture_path", PUBLIC_FIXTURE_PATHS, ids=lambda p: p.name)
    def test_public_fixture_entries_have_schema_name(self, fixture_path):
        """Public fixture JSON objects must declare _schema_name: public."""
        if not fixture_path.exists():
            pytest.skip(f"File missing: {fixture_path}")
        data = json.loads(fixture_path.read_text())
        for entry in data:
            assert "_schema_name" in entry, (
                f"Missing '_schema_name' in {entry} ({fixture_path.name})"
            )
            assert entry["_schema_name"] == "public", f"Unexpected schema in {entry}"


class TestFixtureSeedersSchemaConfiguration:
    """Validate that production fixture seeder classes have correct metadata."""

    def test_configuration_seeders_are_public_tenant_type(self):
        """Configuration seeder must be registered as a fixture seeder."""
        meta = getattr(ConfigurationSeeder, "Meta", None)
        assert meta is not None
        assert meta.is_fixture is True

    def test_customer_preference_type_seeder_is_organization_tenant_type(self):
        """CustomerPreferenceTypeSeeder without explicit schema_name resolves to ALL_SCHEMAS."""
        meta = getattr(CustomerPreferenceTypeSeeder, "Meta", None)
        assert meta is not None
        assert meta.tenant_type == settings.TENANT_TYPE_ORGANIZATION
        instance = CustomerPreferenceTypeSeeder()
        assert instance.schema_name == CustomerPreferenceTypeSeeder.ALL_SCHEMAS


class TestDevSetupJSONFiles:
    """Validate that all dev setup JSON files exist and are valid."""

    DEV_PATHS = [
        SETUP_DIR / "tenants" / "tenants.json",
        SETUP_DIR / "users" / "dev_users" / "users.json",
        SETUP_DIR / "crm" / "dev_customer" / "customers.json",
        SETUP_DIR / "crm" / "dev_customer_phone" / "phones.json",
        SETUP_DIR / "crm" / "dev_customer_email" / "emails.json",
        SETUP_DIR / "crm" / "dev_customer_address" / "addresses.json",
        SETUP_DIR / "invoices" / "dev_billing_organization" / "organizations.json",
        SETUP_DIR / "invoices" / "dev_organization_email" / "emails.json",
        SETUP_DIR / "invoices" / "dev_organization_phone" / "phones.json",
        SETUP_DIR / "invoices" / "dev_invoice_party" / "parties.json",
        SETUP_DIR / "invoices" / "dev_invoice_party_email" / "emails.json",
        SETUP_DIR / "invoices" / "dev_invoice_party_phone" / "phones.json",
        SETUP_DIR / "invoices" / "dev_invoice_item" / "items.json",
    ]

    @pytest.mark.parametrize(
        "dev_path", DEV_PATHS, ids=lambda p: str(p.relative_to(SETUP_DIR))
    )
    def test_dev_json_exists(self, dev_path):
        """Each dev setup JSON file must exist."""
        assert dev_path.exists(), f"Missing dev fixture: {dev_path}"

    @pytest.mark.parametrize(
        "dev_path", DEV_PATHS, ids=lambda p: str(p.relative_to(SETUP_DIR))
    )
    def test_dev_json_is_valid(self, dev_path):
        """Each dev JSON file must be parseable and non-empty."""
        if not dev_path.exists():
            pytest.skip(f"File missing: {dev_path}")

        data = json.loads(dev_path.read_text())
        assert isinstance(data, list)
        assert len(data) > 0

    def test_dev_tenants_have_schema_definition(self):
        """Dev tenants should define tenant configurations."""
        path = SETUP_DIR / "tenants" / "tenants.json"
        data = json.loads(path.read_text())
        schemas = {entry["schema_name"] for entry in data}
        assert "private" in schemas

    def test_dev_users_cover_superusers_and_regular(self):
        """Dev users should define superuser and regular users."""
        path = SETUP_DIR / "users" / "dev_users" / "users.json"
        data = json.loads(path.read_text())
        superusers = [u for u in data if u.get("create_superuser")]
        regular_users = [u for u in data if not u.get("create_superuser")]
        assert len(superusers) >= 1
        assert len(regular_users) >= 1
