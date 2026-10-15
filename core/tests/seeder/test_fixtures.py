import json
import pathlib

import pytest

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
        / "configurations.json",
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
        """Each fixture JSON file must be parseable and contain a list."""
        if not fixture_path.exists():
            pytest.skip(f"File missing: {fixture_path}")

        data = json.loads(fixture_path.read_text())
        assert isinstance(
            data, list
        ), f"{fixture_path.name} should contain a JSON array"
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

    def test_configuration_entries_have_required_fields(self):
        """Configuration fixture entries must have name, interface_type, details."""
        path = (
            APPS_DIR
            / "configurations"
            / "fixtures"
            / "configuration"
            / "configurations.json"
        )
        data = json.loads(path.read_text())
        for entry in data:
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


class TestDevSetupJSONFiles:
    """Validate that all dev setup JSON files exist and are valid."""

    DEV_PATHS = [
        SETUP_DIR / "tenants" / "dev_tenant" / "tenants.json",
        SETUP_DIR / "tenants" / "dev_tenant" / "domains.json",
        SETUP_DIR / "tenants" / "dev_user" / "users.json",
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

    def test_dev_tenants_have_both_schemas(self):
        """Dev tenants should include both public and private schemas."""
        path = SETUP_DIR / "tenants" / "dev_tenant" / "tenants.json"
        data = json.loads(path.read_text())
        schemas = {entry["schema_name"] for entry in data}
        assert "public" in schemas
        assert "private" in schemas

    def test_dev_users_cover_both_tenants(self):
        """Dev users should have entries for both public and private tenants."""
        path = SETUP_DIR / "tenants" / "dev_user" / "users.json"
        data = json.loads(path.read_text())
        schemas = {entry["tenant_schema"] for entry in data}
        assert "public" in schemas
        assert "private" in schemas

    def test_dev_users_have_admin_and_regular(self):
        """Each tenant should have an admin and a regular user."""
        path = SETUP_DIR / "tenants" / "dev_user" / "users.json"
        data = json.loads(path.read_text())

        for schema in ["public", "private"]:
            tenant_users = [u for u in data if u["tenant_schema"] == schema]
            staff_users = [u for u in tenant_users if u["is_staff"]]
            regular_users = [u for u in tenant_users if not u["is_staff"]]
            assert len(staff_users) >= 1, f"No admin user for {schema}"
            assert len(regular_users) >= 1, f"No regular user for {schema}"

    def test_dev_users_email_matches_tenant_domain(self):
        """User emails should match their tenant domain."""
        path = SETUP_DIR / "tenants" / "dev_user" / "users.json"
        data = json.loads(path.read_text())
        for user in data:
            domain = user["tenant_schema"] + ".localhost"
            assert user["email"].endswith(
                f"@{domain}"
            ), f"User email {user['email']} doesn't match domain {domain}"

    def test_dev_customers_cover_both_tenants(self):
        """Dev customers should have entries for both tenants."""
        path = SETUP_DIR / "crm" / "dev_customer" / "customers.json"
        data = json.loads(path.read_text())
        schemas = {entry["tenant_schema"] for entry in data}
        assert "public" in schemas
        assert "private" in schemas

    def test_dev_invoice_items_cover_both_tenants(self):
        """Dev invoice items should exist for both tenants."""
        path = SETUP_DIR / "invoices" / "dev_invoice_item" / "items.json"
        data = json.loads(path.read_text())
        schemas = {entry["tenant_schema"] for entry in data}
        assert "public" in schemas
        assert "private" in schemas
