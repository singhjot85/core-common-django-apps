"""
Utility functions for the Users application.

Provides post-authentication redirect destination resolution adhering to
in-app path restrictions and open redirect protection.
"""

import json
import typing

from django.conf import settings
from django.utils.http import url_has_allowed_host_and_scheme

from core.apps.users import app_settings


def get_auth_redirect_url(request: typing.Any) -> str:
    """
    Resolve post-authentication redirect destination URL safely.

    Checks ``next`` in request payload and query params, verifying that the target
    is a safe in-app URL to prevent open redirects.
    Falls back to LOGIN_REDIRECT_URL or root ("/").

    Args:
        request: The incoming DRF or Django HTTP request.

    Returns:
        str: Validated, safe redirect path string.
    """
    target_candidate = None
    if hasattr(request, "data") and isinstance(request.data, dict):
        target_candidate = request.data.get("next")
    elif hasattr(request, "POST") and request.POST.get("next"):
        target_candidate = request.POST.get("next")
    elif getattr(request, "body", None):
        try:
            payload = json.loads(request.body)
            if isinstance(payload, dict):
                target_candidate = payload.get("next")
        except Exception:
            target_candidate = None

    if not target_candidate and hasattr(request, "GET"):
        target_candidate = request.GET.get("next")

    fallback = getattr(settings, "LOGIN_REDIRECT_URL", "/")

    if target_candidate and isinstance(target_candidate, str):
        target = target_candidate.strip()
        if target:
            if app_settings.ONLY_ALLOW_IN_APP_REDIRECTS:
                allowed_hosts = (
                    {request.get_host()} if hasattr(request, "get_host") else None
                )
            else:
                allowed_hosts = set(getattr(settings, "ALLOWED_HOSTS", [])) or None

            require_https = (
                request.is_secure() if hasattr(request, "is_secure") else False
            )
            if url_has_allowed_host_and_scheme(
                url=target,
                allowed_hosts=allowed_hosts,
                require_https=require_https,
            ):
                return target

    return str(fallback)
