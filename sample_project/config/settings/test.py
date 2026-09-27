from core.config.settings.base import *  # noqa: F401

DEBUG = False
TESTING = True
DJANGO_ENV = "test"

# -----------------------------------------
# DATABASE CONFIGURATION
# Why a separate test database?
# - Complete isolation from development data
# - django-tenants schema operations won't affect dev

# To keep the DB locally without breaking CI/CD pipelines,
# run your tests locally with: `pytest --keepdb`

# -----------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django_tenants.postgresql_backend",
        "NAME": "pytest_db",
        "USER": DATABASE_USER,
        "PASSWORD": DATABASE_PASSWORD,
        "HOST": DATABASE_HOST,
        "PORT": DATABASE_PORT,
        "TEST": {
            "NAME": "pytest_db",  # Keep persistent test database
            "TEMPLATE": "template1",
        },
    },
}


# -----------------------------------------
# DJANGO-TENANTS CONFIGURATION
# -----------------------------------------
# DATABASE_ROUTERS = ('django_tenants.routers.TenantSyncRouter',)
# TENANT_MODEL = f"{TENANT_APP_NAME}.{TENANT_MODEL_NAME}"
# TENANT_DOMAIN_MODEL = f"{TENANT_APP_NAME}.{DOMAIN_MODEL_NAME}"
TENANT_SCHEMA_NAME = "test_schema"

# -----------------------------------------
# CELERY CONFIGURATION
# Why ALWAYS_EAGER?
# - Tasks execute immediately in the same process
# - No need for a running worker during tests
# - Exceptions surface directly in test output
# - Alternative: pytest-celery (spawns real workers, more complex)
# -----------------------------------------
CELERY_TASK_ALWAYS_EAGER = True  # Run tasks synchronously
CELERY_TASK_EAGER_PROPAGATES = True  # Don't hide exceptions
CELERY_BROKER_URL = get_broker_url()

# -----------------------------------------
# CACHE CONFIGURATION
# Simply using LocMemCache, no external dependency and cache setup required.
# -----------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-cache",
    }
}

# -----------------------------------------
# PERFORMANCE OPTIMIZATIONS
# Why MD5 hasher?
# - Default hashers (bcrypt/PBKDF2) are deliberately slow for security
# - Tests don't need password security, they need speed
# - MD5 is fast, saves ~0.5s per user creation
# -----------------------------------------
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# -----------------------------------------
# DISABLED FOR TESTS
# -----------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# TODO: Not sure about this setting, need to revisit this
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
}
