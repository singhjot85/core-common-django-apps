from core.config.settings.base import *  # noqa: F401

DATABASE_ROUTERS = ()  # Clear out db-routing for django's deafult
PUBLIC_SCHEMA_URLCONF = None  # Clear out public-url config for single-tenant
SHARED_APPS = TENANT_APPS = []  # Clear out any djano-tenant apps registerd by core
INSTALLED_APPS -= [TENANT_APPS]  # Remove tenants app from installed apps
