import os

from core.config.celery.base import TenantAwareCeleryApp

# Setup django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.config.settings.base")

PROJECT_NAME = os.getenv("PROJECT_NAME", "core")

# Celery app object initialized to create celery app
app = TenantAwareCeleryApp(PROJECT_NAME)

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()
