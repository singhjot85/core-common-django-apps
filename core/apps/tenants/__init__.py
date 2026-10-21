import typing

from django.apps import apps as django_apps
from django.conf import settings

if typing.TYPE_CHECKING:
    from core.apps.tenants.models_abstract import (
        AbstractDomain,
        AbstractTenantBranding,
        AbstractTenantContactInfo,
        AbstractTenants,
    )


def get_tenant_model():
    """Returns the tenant model that is active in this project."""
    return typing.cast(
        type["AbstractTenants"],
        django_apps.get_model(settings.TENANTS_TENANT_MODEL, require_ready=False),
    )


def get_domain_model():
    """Returns the tenant domain model that is active in this project."""
    return typing.cast(
        type["AbstractDomain"],
        django_apps.get_model(settings.TENANTS_DOMAIN_MODEL, require_ready=False),
    )


def get_tenant_contact_info_model():
    """Returns the tenant contact info model that is active in this project."""
    return typing.cast(
        type["AbstractTenantContactInfo"],
        django_apps.get_model(settings.TENANTS_CONTACT_INFO_MODEL, require_ready=False),
    )


def get_tenant_branding_model():
    """Returns the tenant branding model that is active in this project."""
    return typing.cast(
        type["AbstractTenantBranding"],
        django_apps.get_model(settings.TENANTS_BRANDING_MODEL, require_ready=False),
    )
