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


@pytest.fixture(scope="session")
def django_db_setup(django_test_environment, django_db_blocker):
    """
    Session-scoped DB setup: provision the test tenant and schema exactly once
    per pytest session.

    Runs outside any per-test transaction, so the DDL issued by ``create_schema``
    (CREATE SCHEMA IF NOT EXISTS …) never competes with the savepoint-rollback
    mechanism that pytest-django uses between tests. This eliminates the
    deadlock on ``tenants_tenants_schema_name_key`` that occurs when DDL is
    executed inside a per-test transaction boundary.
    """
    Tenant: type["AbstractTenants"] = get_tenant_model()
    Domain: type["AbstractDomain"] = get_tenant_domain_model()

    with django_db_blocker.unblock():
        with schema_context(get_public_schema_name()):
            tenant, _ = Tenant.objects.get_or_create(
                schema_name=tenant_schema_name,
                defaults={
                    "label": " ".join(tenant_schema_name.split("_")).title(),
                    "is_active": True,
                    "status": "ready",
                },
            )
            if tenant.status != "ready":
                tenant.status = "ready"
                tenant.save(update_fields=["status"])
            Domain.objects.update_or_create(
                domain="localhost",
                defaults={"tenant": tenant, "is_primary": True},
            )
            tenant.create_schema(check_if_exists=True, sync_schema=True, verbosity=0)


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
        with schema_context(tenant_schema_name):
            yield
    else:
        yield
