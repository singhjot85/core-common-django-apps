"""
Runtime checks to validate and generate runtime settings
"""

from django.conf import settings
from django.db import models


def is_multi_tenant():
    """
    Check if the current env is multi-tenant.
    """
    return "django_tenants" in settings.INSTALLED_APPS


def is_production():
    """
    Check if current env is production.
    """
    return not settings.DEBUG and getattr(settings, "DJANGO_ENV", None) == "production"


def is_development():
    """
    Check if current env is development.
    """
    return not is_production()


def is_model(kls):
    """
    Validate that the given class is a django models class
    """
    if isinstance(kls, models.base.ModelBase) or (
        isinstance(kls, type) and issubclass(kls, models.Model)
    ):
        return True

    return False
