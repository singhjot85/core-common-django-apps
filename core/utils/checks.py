"""
Runtime checks to validate and generate runtime settings
"""

import os

from django.conf import settings
from django.db import connection, models


def is_multi_tenant():
    """
    Check if the current env is multi-tenant.
    """
    return "django_tenants" in settings.INSTALLED_APPS


def is_production() -> bool:
    """
    Check if the current environment is production.

    Returns:
        bool: True if production environment with DEBUG=False.
    """
    if settings.configured:
        return (
            not settings.DEBUG and getattr(settings, "DJANGO_ENV", None) == "production"
        )

    debug = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
    return not debug and os.getenv("DJANGO_ENV", "dev") == "production"


def is_development() -> bool:
    """
    Check if the current environment is development.

    Returns:
        bool: True if not in production environment.
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


def is_public():
    """
    Check if current schema is public schema
    """
    return connection.schema_name == getattr(settings, "PUBLIC_SCHEMA_NAME", "public")
