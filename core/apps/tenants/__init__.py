import typing

from django.apps import apps as django_apps
from django.conf import settings

if typing.TYPE_CHECKING:
    from core.apps.tenants.models_abstract import AbstractTenants


def get_tenant_model():
    """
    Returns the tenant model that is active in this project.
    """

    return typing.cast(
        type["AbstractTenants"],
        django_apps.get_model(settings.TENANTS_TENANT_MODEL, require_ready=False),
    )


def get_tenant_configuration():
    """ """
