from .app import app, app as celery_app

__all__ = ("celery_app", "app")
