import os

from django.core.exceptions import ImproperlyConfigured

# -----------------------------
#   POSTGRESQL Database Settings
# -----------------------------
DATABASE_NAME = os.getenv("POSTGRES_DB")
DATABASE_USER = os.getenv("POSTGRES_USER")
DATABASE_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DATABASE_HOST = os.getenv("POSTGRES_HOST")
DATABASE_PORT = os.getenv("POSTGRES_PORT")


# -----------------------------
#   Redis/Valkey Database Settings
# -----------------------------
CACHE_PROTCOL = os.getenv("CACHE_PROTCOL", "redis")
CACHE_HOST = os.getenv("CACHE_HOST", "unfo_cache")
CACHE_PORT = os.getenv("CACHE_PORT", "6379")
CACHE_DATABASE = os.getenv("CACHE_DATABASE", 0)


def get_cache_url():
    if not any([CACHE_PROTCOL, CACHE_HOST, CACHE_PORT]):
        raise ImproperlyConfigured("Cache url is incorrect")

    return f"{CACHE_PROTCOL}://{CACHE_HOST}:{CACHE_PORT}/{CACHE_DATABASE}"


def get_cache_ops():
    CACHE_BACKEND = None
    RESOLVED_CACHE_OPTIONS = None

    if CACHE_PROTCOL == "valkey":
        CACHE_BACKEND = "django_valkey.cluster_cache.cache.ClusterValkeyCache"
        RESOLVED_CACHE_OPTIONS = "django_valkey.client.DefaultClient"

    elif CACHE_PROTCOL == "redis":  # Redis cold-swap readiness
        CACHE_BACKEND = "django_redis.cache.RedisCache"
        RESOLVED_CACHE_OPTIONS = {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "PICKLED_VERSION": 5,
        }

    else:
        raise ImproperlyConfigured(f"Invalid Cache provider [{CACHE_PROTCOL}].")

    return CACHE_BACKEND, RESOLVED_CACHE_OPTIONS
