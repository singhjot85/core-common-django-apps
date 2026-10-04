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

# CRM App
CRM_APP = "core.apps.crm"
CRM_CUSTOMER_MODEL = "crm.Customer"
CRM_CUSTOMER_PHONE_MODEL = "crm.CustomerPhone"
CRM_CUSTOMER_EMAIL_MODEL = "crm.CustomerEmail"
CRM_CUSTOMER_ADDRESS_MODEL = "crm.CustomerAddress"
CRM_CUSTOMER_IDENTIFICATION_MODEL = "crm.CustomerIdentification"
CRM_CUSTOMER_PREFERENCE_TYPE_MODEL = "crm.CustomerPreferenceType"
CRM_CUSTOMER_PREFERENCE_MODEL = "crm.CustomerPreference"


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
    CONFIGURATION_APP,
    CRM_APP,
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
    CRM_APP,
    # "apps.customer_management",
    # "apps.payments_management",
    # "apps.setup",
    # "apps.notifications",
]
