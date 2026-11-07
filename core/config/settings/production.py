"""
Production settings for core-common-django-apps.

Configures Cloudflare R2 (S3-compatible) object storage via django-storages,
disables debug mode, and enforces production security defaults.
"""

import os

from core.config.settings.base import *  # noqa: F401

DEBUG = False

# --------------------------------------------------
# Cloudflare R2 Object Storage (S3-Compatible)
# --------------------------------------------------
CLOUDFLARE_R2_ACCOUNT_ID = os.getenv("CLOUDFLARE_R2_ACCOUNT_ID", "")
CLOUDFLARE_R2_BUCKET_NAME = os.getenv(
    "CLOUDFLARE_R2_BUCKET_NAME", os.getenv("AWS_STORAGE_BUCKET_NAME", "")
)
CLOUDFLARE_R2_ACCESS_KEY_ID = os.getenv(
    "CLOUDFLARE_R2_ACCESS_KEY_ID", os.getenv("AWS_ACCESS_KEY_ID", "")
)
CLOUDFLARE_R2_SECRET_ACCESS_KEY = os.getenv(
    "CLOUDFLARE_R2_SECRET_ACCESS_KEY", os.getenv("AWS_SECRET_ACCESS_KEY", "")
)
CLOUDFLARE_R2_CUSTOM_DOMAIN = os.getenv(
    "CLOUDFLARE_R2_CUSTOM_DOMAIN", os.getenv("AWS_S3_CUSTOM_DOMAIN", "")
)
CLOUDFLARE_R2_ENDPOINT_URL = os.getenv(
    "CLOUDFLARE_R2_ENDPOINT_URL",
    f"https://{CLOUDFLARE_R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
    if CLOUDFLARE_R2_ACCOUNT_ID
    else "",
)

r2_options = {
    "bucket_name": CLOUDFLARE_R2_BUCKET_NAME,
    "endpoint_url": CLOUDFLARE_R2_ENDPOINT_URL,
    "region_name": "auto",
    "signature_version": "s3v4",
    "file_overwrite": False,
    "default_acl": None,
    "querystring_auth": True,
}

if CLOUDFLARE_R2_ACCESS_KEY_ID and CLOUDFLARE_R2_SECRET_ACCESS_KEY:
    r2_options["access_key"] = CLOUDFLARE_R2_ACCESS_KEY_ID
    r2_options["secret_key"] = CLOUDFLARE_R2_SECRET_ACCESS_KEY

if CLOUDFLARE_R2_CUSTOM_DOMAIN:
    r2_options["custom_domain"] = CLOUDFLARE_R2_CUSTOM_DOMAIN
    MEDIA_URL = f"https://{CLOUDFLARE_R2_CUSTOM_DOMAIN}/"
else:
    MEDIA_URL = "/media/"

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": r2_options,
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
