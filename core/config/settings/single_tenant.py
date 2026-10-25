"""
Single-tenant settings module for core applications.

Overrides multi-tenant settings (django-tenants) to configure standard single-database
Django deployments without tenant routers or multi-tenant schema isolation.
"""

from core.config.settings.base import *  # noqa: F401

DATABASE_ROUTERS = ()  # Clear out db-routing for django's default
PUBLIC_SCHEMA_URLCONF = None  # Clear out public-url config for single-tenant
SHARED_APPS = []  # Clear out any django-tenant apps registered by core
TENANT_APPS = []

# Remove django-tenants and tenants app from installed apps and project apps
INSTALLED_APPS = [
    app for app in INSTALLED_APPS if app not in ("django_tenants", TENANTS_APP)
]
PROJECT_APPS = [
    app for app in PROJECT_APPS if app not in ("django_tenants", TENANTS_APP)
]
MIDDLEWARE = [m for m in MIDDLEWARE if not m.startswith("django_tenants")]
