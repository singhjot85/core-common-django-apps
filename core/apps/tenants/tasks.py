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
def provision_tenant_schema(self, tenant_id: str):
    """
    Provision a tenant schema for creation, the scehma is not created on main thread its offloaded to an task queue
    """
    if not tenant_id:
        LOGGER.error("Tenant id not provided.")
        return

    TenantModel: type["Tenants"] = get_tenant_model()

    try:
        tenant = TenantModel.objects.get(id=tenant_id)
    except TenantModel.DoesNotExist:
        LOGGER.error(f"Tenant {tenant_id} not found.")
        return

    if tenant.status == TenantStatus.READY:
        LOGGER.info(f"Tenant {tenant.schema_name} is already provisioned and READY.")
        return

    try:
        LOGGER.info(f"Starting schema creation for tenant: {tenant.schema_name}")

        # 1. Create Postgres schema if not exists
        # 2. Run migrate_schemas command targeting only this schema
        tenant.create_schema(check_if_exists=True, sync_schema=True, verbosity=1)

        # 3. Mark tenant as READY
        TenantModel.objects.filter(id=tenant.id).update(status=TenantStatus.READY)
        LOGGER.info(f"Tenant {tenant.schema_name} provisioned successfully.")

    except Exception as exc:
        LOGGER.exception(
            f"Failed to migrate schema for tenant {tenant.schema_name}: {exc}"
        )
        TenantModel.objects.filter(id=tenant.id).update(status=TenantStatus.FAILED)
        raise exc
