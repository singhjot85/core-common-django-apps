"""
This file contain the celery app used in project, the app is overriden to provide tenant context to celery tasks.

NOTE: Never do a dependecy import in this file, or any import that might trigger django settings,
    Make sure you do lazy imports only, if needed do after setting's import
"""

from celery import Celery
from celery.contrib.django.task import DjangoTask
from celery.signals import task_postrun, task_prerun
from django.db import connection


class TenantAwareTask(DjangoTask):
    """
    Custom Task class that ensures the tenant schema context is preserved
    during task execution.
    """

    abstract = True

    def _add_current_schema(self, kwargs: dict):
        kwargs.setdefault("_schema_name", connection.schema_name)

    def apply_async(self, args=None, kwargs=None, *arg, **options):
        kwargs = kwargs or {}
        self._add_current_schema(kwargs)
        return super().apply_async(args, kwargs, *arg, **options)

    def apply(self, args=None, kwargs=None, *arg, **options):
        kwargs = kwargs or {}
        self._add_current_schema(kwargs)
        return super().apply(args, kwargs, *arg, **options)


def switch_schema_context(task, kwargs, **kw):
    """Set the correct database connection, before the task runs."""
    from django_tenants.utils import get_public_schema_name, get_tenant_model

    old_schema = (connection.schema_name, connection.include_public_schema)
    setattr(task, "_old_schema", old_schema)

    schema = kwargs.pop("_schema_name", get_public_schema_name())

    if connection.schema_name == schema:
        return

    if connection.schema_name != get_public_schema_name():
        connection.set_schema_to_public()

    tenant = get_tenant_model().objects.get(schema_name=schema)
    connection.set_tenant(tenant, include_public=True)


def restore_schema_context(task, **kw):
    """Restore the original schema, after the task runs."""
    from django_tenants.utils import get_public_schema_name

    schema_name, include_public = getattr(
        task, "_old_schema", (get_public_schema_name, True)
    )

    if connection.schema_name == schema_name:
        return

    connection.set_schema(schema_name, include_public=include_public)


task_prerun.connect(
    switch_schema_context, sender=None, dispatch_uid="custom_switch_schema_context"
)

task_postrun.connect(
    restore_schema_context, sender=None, dispatch_uid="custom_restore_schema_context"
)


class TenantAwareCeleryApp(Celery):
    """
    Custom Celery App that automatically injects the current tenant's schema
    into the task arguments before sending it to the broker.
    """

    task_cls = "config.celery.base.TenantAwareTask"

    def create_task_cls(self):
        return self.subclass_with_self(
            "config.celery.base.TenantAwareTask",
            abstract=True,
            name="TenantAwareTask",
            attribute="_app",
        )
