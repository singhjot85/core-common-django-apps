import os
from pathlib import Path

from .base_models import *
from .databases import *
from .task_queues import *

# ------------------
#  Custom Settings
# ------------------
APP_NAME = "apps"
PROJECT_NAME = os.getenv("PROJECT_NAME")
PROJECT_LABEL = os.getenv("PROJECT_LABEL")
DJANGO_ENV = os.getenv("DJANGO_ENV", "dev")

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # Path to /backend
APP_DIR = os.path.join(BASE_DIR, APP_NAME)  # Path to /backend/apps

SENSITIVE_PHRASES = os.getenv("SENSITIVE_PHRASES", [])
APPLICATION_TIMEZONE = os.getenv("TIME_ZONE", "UTC")


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

STATIC_URL = "static/"
ROOT_URLCONF = "config.urls"
PUBLIC_SCHEMA_URLCONF = "config.public_urls"

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
    "default": {
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

CACHE_SMALL_SMALL_TIMEOUT = os.getenv("CACHE_SMALL_SMALL_TIMEOUT", 30)  # 30 seconds
CACHE_SMALL_TIMEOUT = os.getenv("CACHE_SMALL_TIMEOUT", 30 * 2)  # 2 mins
CACHE_LARGE_TIMEOUT = os.getenv("CACHE_LARGE_TIMEOUT", 60 * 20)  # 20 mins
CACHE_LARGE_LARGE_TIMEOUT = os.getenv("CACHE_LARGE_LARGE_TIMEOUT", 60 * 60)  # 1 hour

CACHES = {
    "default": {
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

CELERY_TIMEZONE = APPLICATION_TIMEZONE

CELERY_TASK_ALWAYS_EAGER = False  # Eager task run on same caller process
CELERY_TASK_TRACK_STARTED = True  # Save's `Started` as one of the task status.
CELERY_TASK_TIME_LIMIT = TASK_TIME_LIMIT
CELERY_TASK_SOFT_TIME_LIMIT = TASK_SOFT_TIME_LIMIT

# Writes extended results to backend (name, args, kwargs, worker, retries, queue, delivery_info).
CELERY_RESULT_EXTENDED = True
CELERY_DEFAULT_TASK_QUEUE = DEFAULT_TASK_QUEUE_NAME

# Need to define this explicilty fo celery
TENANT_DB_ALIAS = "default"

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
        ],
        "APP_DIRS": True,
        "OPTIONS": {
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
#   dj-rest-auth
# -----------------------------
REST_AUTH = {"USER_DETAILS_SERIALIZER": "core.apps.tenants.serializers.UserSerializer"}


# ------------------
#  drf settings
# ------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
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
