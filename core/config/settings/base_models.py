# ----------------------------
# Model and App Naming
# Naming Convention:
#   APPS: APP_<app_name>,
#   MODELS: <app_name>_<model_name>
# ----------------------------


# Django Tenants App
TENANTS_APP = "core.apps.tenants"
TENANTS_TENANT_MODEL = "tenants.Tenants"
TENANTS_DOMAIN_MODEL = "tenants.Domain"
TENANTS_CONTACT_INFO_MODEL = "tenants.TenantContactInfo"
TENANTS_BRANDING_MODEL = "tenants.TenantBranding"

# Configuration App
CONFIGURATION_APP = "core.apps.configurations"
CONFIGURATIONS_CONFIGURATION_MODEL = "configurations.Configuration"
CONFIGURATIONS_CONFIGURATION_SCHEMA_MODEL = "configurations.ConfigurationSchema"
CONFIGURATIONS_TENANT_CONFIGURATION_MODEL = "configurations.TenantConfiguration"


# ----------------------------
#   Runtime App Classification
# ----------------------------

SHARED_DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]
PUBLIC_ONLY_DJANGO_APPS = []
TENANT_ONLY_DJANGO_APPS = []

SHARED_EXTRA_DEPENDENCIES = [
    "django_tenants",
    "rest_framework",
    # "rest_framework.authtoken",
    # "dj_rest_auth",
    "constance",
]

PUBLIC_ONLY_EXTRA_DEPENDENCIES = [
    "django_celery_results",
]

TENANT_ONLY_EXTRA_DEPENDENCIES = []

PROJECT_APPS = [
    TENANTS_APP,
    # APP_CRM,
    # "apps.tenants",
    # "apps.setup",
    # "apps.customer_management",
    # "apps.payments_management",
    # "apps.notifications",
]


# -----------------------------
#   Database App Classification
# -----------------------------
DJANGO_TENANT_PUBLIC_APPS = [
    *SHARED_DJANGO_APPS,
    *PUBLIC_ONLY_DJANGO_APPS,
    *SHARED_EXTRA_DEPENDENCIES,
    *PUBLIC_ONLY_EXTRA_DEPENDENCIES,
    TENANTS_APP,
    # "apps.setup",
]

DJANGO_TENANT_PRIVATE_APPS = [
    *SHARED_DJANGO_APPS,
    *TENANT_ONLY_DJANGO_APPS,
    *SHARED_EXTRA_DEPENDENCIES,
    *TENANT_ONLY_EXTRA_DEPENDENCIES,
    # APP_CRM,
    # "apps.customer_management",
    # "apps.payments_management",
    # "apps.setup",
    # "apps.notifications",
]
