import os

from django.conf import settings

from config.celery.base import TenantAwareCeleryApp

# Setup django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")

PROJECT_NAME = settings.PROJECT_NAME

# Celery app object intialized to create celery app
app = TenantAwareCeleryApp(PROJECT_NAME)

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks(packages=settings.INSTALLED_APPS)
