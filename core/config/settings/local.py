"""
Local development settings for core-common-django-apps.

Provides standard local development defaults (DEBUG=True, permissive ALLOWED_HOSTS,
local filesystem media storage in media/ under BASE_DIR) so host projects do not
have to define the entire local configuration from scratch.
"""

import os

from core.config.settings.base import *  # noqa: F401

DEBUG = True
ALLOWED_HOSTS = ["*"]

# -----------------------------
#   Local Media Storage (Filesystem)
# -----------------------------
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# -----------------------------
#   Local Request Logging Middleware
# -----------------------------
MIDDLEWARE = [
    "core.config.middlewares.request_logging.RequestLoggingMiddleware",
    *MIDDLEWARE,
]

# Disable sensitive content masking in local development for easier UI/mobile debugging
DISABLE_SENSITIVE_CONTENT_FILTER = True
