import os

from django.core.exceptions import ImproperlyConfigured

# -----------------------------
#   Celery Broker Settings
# -----------------------------
BROKER_PROTOCOL = os.getenv("BROKER_PROTOCOL", "redis")
BROKER_HOST = os.getenv("BROKER_HOST", "broker")
BROKER_PORT = os.getenv("BROKER_PORT", "6378")
BROKER_DATABASE = os.getenv("BROKER_DATABASE", 0)


def get_broker_url():
    if not all([BROKER_PROTOCOL, BROKER_HOST, BROKER_PORT]):
        raise ImproperlyConfigured("Celery Broker url is incorrect")

    return f"{BROKER_PROTOCOL}://{BROKER_HOST}:{BROKER_PORT}/{BROKER_DATABASE}"


DEFAULT_TASK_QUEUE_NAME = os.getenv("CELERY_DEFAULT_TASK_QUEUE", "celery_default_queue")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "django-db")
TASK_TIME_LIMIT = os.getenv("CELERY_TASK_TIME_LIMIT", 9 * 60)
TASK_SOFT_TIME_LIMIT = os.getenv("CELERY_TASK_SOFT_TIME_LIMIT", 8 * 60)
TASK_DEFAULT_RETRY_DELAY = int(os.getenv("CELERY_TASK_DEFAULT_RETRY_DELAY", 60))
TASK_MAX_RETRIES = int(os.getenv("CELERY_TASK_MAX_RETRIES", 3))
TASK_AUTORETRY_FOR = (Exception,)
