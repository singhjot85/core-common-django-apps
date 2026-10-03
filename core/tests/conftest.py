import typing

import pytest
from django.conf import settings
from django_tenants.utils import (
    get_public_schema_name,
    get_tenant_domain_model,
    get_tenant_model,
    schema_context,
)

if typing.TYPE_CHECKING:
    from core.apps.tenants.models_abstract import AbstractDomain, AbstractTenants

tenant_schema_name = getattr(settings, "TENANT_SCHEMA_NAME", "test_schema")


@pytest.fixture
def setup_test_tenant(db):
    """
    Create and provision the multi-tenant db schema for tests.
    """
    Tenant: type["AbstractTenants"] = get_tenant_model()
    Domain: type["AbstractDomain"] = get_tenant_domain_model()

    with schema_context(get_public_schema_name()):
        tenant, _ = Tenant.objects.get_or_create(
            schema_name=tenant_schema_name,
            defaults={
                "label": " ".join(tenant_schema_name.split("_")).title(),
                "is_active": True,
            },
        )
        Domain.objects.get_or_create(
            tenant=tenant,
            domain="localhost",
            defaults={"is_primary": True},
        )
        tenant.create_schema(check_if_exists=True, sync_schema=True, verbosity=0)

    return tenant


@pytest.fixture
def public_schema(db):
    """
    Switch to public schema for tests.
    """
    with schema_context(get_public_schema_name()):
        yield


@pytest.fixture(autouse=True)
def tenant_schema(request):
    """Switch execution context to the test tenant schema for database tests."""
    if "django_db" in request.keywords or "db" in request.fixturenames:
        request.getfixturevalue("setup_test_tenant")
        with schema_context(tenant_schema_name):
            yield
    else:
        yield
