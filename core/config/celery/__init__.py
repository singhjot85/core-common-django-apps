from .app import app
from .app import app as celery_app

__all__ = ("celery_app", "app")
