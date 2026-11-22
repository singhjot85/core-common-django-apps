from django.db import models

from core.apps.tenants.constants import TenantStatus


class TenantQuerySet(models.QuerySet):
    """ """

    def provisioned(self) -> models.QuerySet:
        """ """
        return self.filter(
            is_active=True, is_removed=False, status=TenantStatus.READY.value
        )

    def provisioning(self) -> models.QuerySet:
        """ """
        return self.filter(
            is_active=True, is_removed=False, status=TenantStatus.PROVISIONING.value
        )


class TenantManager(models.Manager.from_queryset(TenantQuerySet)):
    """ """

    pass
