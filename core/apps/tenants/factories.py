"""
Model factories for the tenants application.
"""

import factory

from core.apps.tenants import (
    get_domain_model,
    get_tenant_branding_model,
    get_tenant_contact_info_model,
    get_tenant_model,
)
from core.apps.tenants.constants import (
    TenantContactInfoChoices,
    TenantStatus,
    TenantTypeChoices,
)

Tenant = get_tenant_model()
Domain = get_domain_model()
TenantBranding = get_tenant_branding_model()
TenantContactInfo = get_tenant_contact_info_model()


class TenantFactory(factory.django.DjangoModelFactory):
    """Factory for generating Tenant instances."""

    class Meta:
        model = Tenant

    schema_name = factory.Sequence(lambda n: f"tenant_{n}")
    label = factory.Sequence(lambda n: f"Tenant {n}")
    is_active = True
    status = TenantStatus.READY
    type = TenantTypeChoices.ORGANIZATION


class DomainFactory(factory.django.DjangoModelFactory):
    """Factory for generating Domain instances."""

    class Meta:
        model = Domain

    domain = factory.Sequence(lambda n: f"tenant-{n}.localhost")
    tenant = factory.SubFactory(TenantFactory)
    is_primary = True


class TenantBrandingFactory(factory.django.DjangoModelFactory):
    """Factory for generating TenantBranding instances."""

    class Meta:
        model = TenantBranding

    tenant = factory.SubFactory(TenantFactory)


class TenantContactInfoFactory(factory.django.DjangoModelFactory):
    """Factory for generating TenantContactInfo instances."""

    class Meta:
        model = TenantContactInfo

    tenant = factory.SubFactory(TenantFactory)
    contact_type = TenantContactInfoChoices.EMAIL
    contact_info = factory.LazyFunction(lambda: {"email": "admin@example.com"})
