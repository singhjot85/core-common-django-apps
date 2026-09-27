# ----------------------------
# Model and App Naming
# Naming Convention:
#   APPS: APP_<app_name>,
#   MODELS: <app_name>_<model_name>
# ----------------------------


# Django Tenants App
APP_TENANTS = "apps.tenants"
TENANTS_TENANT = "tenants.Tenants"
TENANTS_DOMAIN = "tenants.Domain"
TENANTS_CONTACT_INFO = "tenants.TenantContactInfo"
TENANTS_CONFIGURATION = "tenants.TenantConfiguration"
TENANTS_BRANDING = "tenants.TenantBranding"


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
    APP_TENANTS,
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
    APP_TENANTS,
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
