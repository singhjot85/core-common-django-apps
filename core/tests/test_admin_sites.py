from core.apps.configurations import get_configuration_model
from core.apps.crm import get_customer_model
from core.apps.invoices import get_billing_organization_model, get_invoice_model
from core.apps.tenants import get_domain_model, get_tenant_model
from core.utils.admin import private_admin_site, public_admin_site


class TestAdminSitesRegistration:
    def test_public_admin_site_registered_models(self):
        """Verify public schema models are registered under public_admin_site."""
        Tenants = get_tenant_model()
        Domain = get_domain_model()
        Configuration = get_configuration_model()

        assert Tenants in public_admin_site._registry
        assert Domain in public_admin_site._registry
        assert Configuration in public_admin_site._registry

        # Tenant-private models should NOT be in public_admin_site
        Customer = get_customer_model()
        Invoice = get_invoice_model()
        assert Customer not in public_admin_site._registry
        assert Invoice not in public_admin_site._registry

    def test_private_admin_site_registered_models(self):
        """Verify tenant schema models are registered under private_admin_site."""
        Customer = get_customer_model()
        Invoice = get_invoice_model()
        BillingOrganization = get_billing_organization_model()

        assert Customer in private_admin_site._registry
        assert Invoice in private_admin_site._registry
        assert BillingOrganization in private_admin_site._registry

        # Public-only tenant management models should NOT be in private_admin_site
        Tenants = get_tenant_model()
        Domain = get_domain_model()
        assert Tenants not in private_admin_site._registry
        assert Domain not in private_admin_site._registry

    def test_admin_site_headers_and_titles(self):
        """Verify titles and headers configured for both admin sites."""
        assert public_admin_site.site_header == "Public Administration"
        assert public_admin_site.site_title == "Public Admin"
        assert public_admin_site.index_title == "Public Portal"

        assert private_admin_site.site_header == "Tenant Administration"
        assert private_admin_site.site_title == "Tenant Admin"
        assert private_admin_site.index_title == "Tenant Portal"
