from core.apps.tenants import models_abstract


class Tenants(models_abstract.AbstractTenants):
    """
    Model for Tenant's and their schema's.
    Swappable model for tenants, allowing for customization and extension of the tenant model.
    """

    class Meta(models_abstract.AbstractTenants.Meta):
        swappable = "TENANTS_TENANT_MODEL"


class Domain(models_abstract.AbstractDomain):
    """
    Model for Backend Domains for tenants.
    Swappable model for domains, allowing for customization and extension of the domain model.
    """

    class Meta(models_abstract.AbstractDomain.Meta):
        swappable = "TENANTS_DOMAIN_MODEL"


class TenantContactInfo(models_abstract.AbstractTenantContactInfo):
    """
    Model for Tenant Contact Information.
    Swappable model for tenant contact information, allowing for customization and extension of the contact info model.
    """

    class Meta(models_abstract.AbstractTenantContactInfo.Meta):
        swappable = "TENANTS_CONTACT_INFO_MODEL"


class TenantBranding(models_abstract.AbstractTenantBranding):
    """
    Model for Tenant Branding.
    Swappable model for tenant branding, allowing for customization and extension of the branding model.
    """

    class Meta(models_abstract.AbstractTenantBranding.Meta):
        swappable = "TENANTS_BRANDING_MODEL"
