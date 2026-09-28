"""
Runtime checks to validate and generate runtime settings
"""

from django.conf import settings


def is_multi_tenant():
    """
    Check if the current env is multi-tenant.
    """
    return "django_tenants" in settings.INSTALLED_APPS


def is_production():
    """
    Check if current env is production.
    """
    return not settings.DEBUG and settings.DJANGO_ENV == "production"
