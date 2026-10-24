import os
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

from core.config.logging import get_logging_config
from core.config.settings.base_models import *
from core.config.settings.databases import *
from core.config.settings.task_queues import *

# ------------------
#  Custom Settings
# ------------------
APP_NAME = "apps"
PROJECT_NAME = os.getenv("PROJECT_NAME")
PROJECT_LABEL = os.getenv("PROJECT_LABEL")
DJANGO_ENV = os.getenv("DJANGO_ENV", "dev")
LOGGING_CONFIG_PATH = "config.logs"

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # Path to /backend
APP_DIR = os.path.join(BASE_DIR, APP_NAME)  # Path to /backend/apps

# -----------------------------
#   Core Framework Directories
# -----------------------------
CORE_BASE_DIR = Path(__file__).resolve().parent.parent.parent
CORE_APP_DIR = os.path.join(CORE_BASE_DIR, APP_NAME)
CORE_SETUP_DIR = os.path.join(CORE_BASE_DIR, "setup")
SANDBOX_TEMPLATES_DIRS = [
    CORE_SETUP_DIR,
    os.path.join(CORE_BASE_DIR, "templates"),
    os.path.join(BASE_DIR, "templates"),
]

SENSITIVE_PHRASES = os.getenv("SENSITIVE_PHRASES", [])
APPLICATION_TIMEZONE = os.getenv("TIME_ZONE", "UTC")
PROJECT_MIGRATION_PATH = f"{PROJECT_NAME}.db_migrations"


# -----------------------------
#   Common Django Settings
# -----------------------------
USE_TZ = True
USE_I18N = True
LANGUAGE_CODE = "en-us"

WSGI_APPLICATION = "config.wsgi.application"
DEBUG = os.getenv("DEBUG", DJANGO_ENV == "dev")
ALLOWED_HOSTS = []

TIME_ZONE = APPLICATION_TIMEZONE
TEMPLATES_DIR = os.path.join(BASE_DIR, "django_templates", "templates")
SECRET_KEY = os.getenv("SECRET_KEY", None)
if not SECRET_KEY:
    if DJANGO_ENV == "production":
        raise ImproperlyConfigured("Secret key not defined for app")
    SECRET_KEY = "django-insecure-core-common-apps-secret-key-default"  # pragma: allowlist secret

LOGGING = get_logging_config(LOGGING_CONFIG_PATH)

STATIC_URL = "/static/"
ROOT_URLCONF = "core.config.urls"
PUBLIC_SCHEMA_URLCONF = "core.config.public_urls"

TENANT_TYPE_PUBLIC = "public"
TENANT_TYPE_ORGANIZATION = "organization"
TENANT_TYPES = {
    TENANT_TYPE_PUBLIC: {
        "label": "Public Tenant",
        "models": [
            *SHARED_DJANGO_APPS,
            *PUBLIC_ONLY_DJANGO_APPS,
            *PUBLIC_ONLY_EXTRA_DEPENDENCIES,
        ],
    },
    TENANT_TYPE_ORGANIZATION: {
        "label": "Organization Tenant",
        "models": [
            *SHARED_DJANGO_APPS,
            *TENANT_ONLY_DJANGO_APPS,
            *TENANT_ONLY_EXTRA_DEPENDENCIES,
        ],
    },
}

TENANT_MODEL = TENANTS_TENANT_MODEL
TENANT_DOMAIN_MODEL = TENANTS_DOMAIN_MODEL

INSTALLED_APPS = [
    *SHARED_DJANGO_APPS,
    *PUBLIC_ONLY_DJANGO_APPS,
    *TENANT_ONLY_DJANGO_APPS,
    *SHARED_EXTRA_DEPENDENCIES,
    *PUBLIC_ONLY_EXTRA_DEPENDENCIES,
    *TENANT_ONLY_EXTRA_DEPENDENCIES,
    *PROJECT_APPS,
]

# -----------------------------
#   Database Configuration
# -----------------------------
SHARED_APPS = DJANGO_TENANT_PUBLIC_APPS
TENANT_APPS = DJANGO_TENANT_PRIVATE_APPS
DATABASE_ROUTERS = ("django_tenants.routers.TenantSyncRouter",)

DATABASES = {
    DEAFULT_DATABASE: {
        "ENGINE": "django_tenants.postgresql_backend",
        "NAME": DATABASE_NAME,
        "USER": DATABASE_USER,
        "PASSWORD": DATABASE_PASSWORD,
        "HOST": DATABASE_HOST,
        "PORT": DATABASE_PORT,
    }
}

# -----------------------------
#   Cache Configuration
# -----------------------------
CACHE_URL = get_cache_url()
CACHE_BACKEND, RESOLVED_CACHE_OPTIONS = get_cache_ops()

CACHES = {
    DEFAULT_CACHE_DATABASE: {
        "BACKEND": CACHE_BACKEND,
        "LOCATION": CACHE_URL,
        "OPTIONS": RESOLVED_CACHE_OPTIONS,
        "IGNORE_EXCEPTIONS": True,
        "TIMEOUT": CACHE_LARGE_TIMEOUT,
    },
}

# -----------------------------
#   Celery Configuration
# UserGuide: https://docs.celeryq.dev/en/latest/userguide/configuration.html#
# -----------------------------
CELERY_BROKER_URL = get_broker_url()
CELERY_RESULT_BACKEND = RESULT_BACKEND

CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

CELERY_MAX_RETRIES = DEFAULT_TASK_RETRY_COUNT
CELERY_DEFAULT_RETRY_DELAY = DEFAULT_TASK_RETRY_DELAY

CELERY_TIMEZONE = APPLICATION_TIMEZONE

CELERY_TASK_ALWAYS_EAGER = False  # Eager task run on same caller process
CELERY_TASK_TRACK_STARTED = True  # Save's `Started` as one of the task status.
CELERY_TASK_TIME_LIMIT = TASK_TIME_LIMIT
CELERY_TASK_SOFT_TIME_LIMIT = TASK_SOFT_TIME_LIMIT

# Writes extended results to backend (name, args, kwargs, worker, retries, queue, delivery_info).
CELERY_RESULT_EXTENDED = True
CELERY_DEFAULT_TASK_QUEUE = DEFAULT_TASK_QUEUE_NAME
CELERY_TASK_MAX_RETRIES = TASK_MAX_RETRIES
CELERY_TASK_DEFAULT_RETRY_DELAY = TASK_DEFAULT_RETRY_DELAY
CELERY_TASK_AUTORETRY_FOR = TASK_AUTORETRY_FOR

# Need to define this explicilty fo celery
TENANT_DB_ALIAS = DEAFULT_DATABASE

# CELERY_TASK_ROUTES = {
#     "task_name": {"queue": "queue_name"}
# }
# CELERY_BEAT_SCHEDULER = "config.beat.CustomDatabaseScheduler"

# -----------------------------
#   Django & Jinja2 Templates
# -----------------------------
TEMPLATES = [
    {
        "BACKEND": "core.utils.jinja2.Jinja2Backend",
        "DIRS": [
            os.path.join(BASE_DIR, "templates"),
            # os.path.join(BASE_DIR.parent, "sample_project", "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            # "loader": "core.utils.jinja2.loaders.SafeDatabaseLoader",
            "environment": "core.utils.jinja2.environment.jinja2_environment",
        },
    },
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [TEMPLATES_DIR],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

# -----------------------------
#   Django Middleware
# -----------------------------
MIDDLEWARE = [
    "django_tenants.middleware.main.TenantMainMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # "backend.config.middlewares.RequestLoggingMiddleware",
]

# -----------------------------
#   Django Password Validators
# -----------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# -----------------------------
#   dj-rest-auth & SimpleJWT
# -----------------------------
REST_AUTH = {
    "USE_JWT": True,
    "TOKEN_MODEL": None,
    "USER_DETAILS_SERIALIZER": "core.apps.users.api.serializers.UserDetailsSerializer",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# TODO: Encrypt and put these in database
GOOGLE_AUTH_CLIENT_ID = os.getenv("GOOGLE_AUTH_CLIENT_ID", "")

# ------------------
#  drf settings
# ------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
}

# ------------------
#  django-mail TODO: Work on email backends
# ------------------
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "")
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ------------------
#  django-constance
# ------------------
CONSTANCE_REDIS_CONNECTION = get_cache_url()

# NOTE: Avoid adding anything to these set them in app_settings
# If the setting is to be made app_wide then only add it here.
CONSTANCE_CONFIG = {}
CONSTANCE_CONFIG_FIELDSETS = {}
