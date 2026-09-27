# core/apps/tenants/tasks.py
import logging
import typing

from celery import shared_task
from django_tenants.utils import get_tenant_model

from core.apps.tenants.constants import TenantStatus

if typing.TYPE_CHECKING:
    from .models import Tenants

LOGGER = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def provision_tenant_schema(self, tenant_id):
    """
    Provision a tenant schema for creation, the scehma is not created on main thread its offloaded to an task queue
    """

    TenantModel: type["Tenants"] = get_tenant_model()
    try:
        tenant = TenantModel.objects.get(id=tenant_id)
    except TenantModel.DoesNotExist:
        LOGGER.error(f"Tenant {tenant_id} not found.")
        return

    try:
        LOGGER.info(f"Starting schema creation for tenant: {tenant.schema_name}")

        # 1. Create Postgres schema if not exists
        # 2. Run migrate_schemas command targeting only this schema
        tenant.create_schema(check_if_exists=True, sync_schema=True, verbosity=1)

        # 3. Mark tenant as READY
        tenant.status = TenantStatus.READY
        tenant.save(update_fields=["status"])
        LOGGER.info(f"Tenant {tenant.schema_name} provisioned successfully.")

    except Exception as exc:
        LOGGER.exception(
            f"Failed to migrate schema for tenant {tenant.schema_name}: {exc}"
        )
        tenant.status = TenantStatus.FAILED
        tenant.save(update_fields=["status"])
        raise exc
