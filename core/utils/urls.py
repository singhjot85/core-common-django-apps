import importlib.util
import logging
import typing

from django.conf import settings
from django.urls import URLPattern, URLResolver, include, path

LOGGER = logging.getLogger(__name__)


def _build_url_path(app_label: str, prefix: str = "api", version: str = "v1") -> str:
    """
    Construct a normalized, versioned URL route path string.

    Args:
        app_label: The short app label (e.g. 'users', 'crm').
        prefix: URL prefix (e.g. 'api'). Defaults to 'api'.
        version: API version string (e.g. 'v1'). Defaults to 'v1'.

    Returns:
        Normalized URL path ending with a forward slash.
    """
    parts = []
    if prefix:
        parts.append(prefix.strip("/"))
    parts.append(app_label.strip("/"))
    if version:
        parts.append(version.strip("/"))

    return f"{'/'.join(parts)}/"


def _has_urls_module(dotted_app_path: str) -> bool:
    """
    Check whether a dotted app path contains a discoverable `urls` module.

    Args:
        dotted_app_path: Dotted module path (e.g. 'core.apps.users').

    Returns:
        True if `<dotted_app_path>.urls` exists and can be imported, False otherwise.
    """
    module_name = f"{dotted_app_path}.urls"
    try:
        spec = importlib.util.find_spec(module_name)
        return spec is not None
    except (ImportError, ValueError, AttributeError):
        return False


def _resolve_app_url_entries(
    app_list: typing.Iterable[str],
    excluded_apps: typing.Iterable[str] | None = None,
    prefix: str = "api",
    version: str = "v1",
) -> tuple[URLPattern | URLResolver, ...]:
    """
    Filter apps, discover their URL modules, and generate Django URL patterns.

    Args:
        app_list: Iterable of dotted app paths to inspect.
        excluded_apps: Iterable of dotted app paths to omit.
        prefix: URL prefix string for generated endpoints.
        version: API version string.

    Returns:
        Tuple of Django URLPattern or URLResolver objects.
    """
    exclusions = set(excluded_apps) if excluded_apps else set()
    url_entries: list[URLPattern | URLResolver] = []

    for dotted_app_path in app_list:
        if dotted_app_path in exclusions:
            continue

        if not _has_urls_module(dotted_app_path):
            LOGGER.debug("Skipping %s: no 'urls' module found.", dotted_app_path)
            continue

        app_label = dotted_app_path.split(".")[-1]
        url_path = _build_url_path(app_label=app_label, prefix=prefix, version=version)
        url_entries.append(path(url_path, include(f"{dotted_app_path}.urls")))

    return tuple(url_entries)


def build_tenant_app_urlpatterns(
    prefix: str = "api",
    version: str = "v1",
) -> tuple[URLPattern | URLResolver, ...]:
    """
    Construct versioned API URL patterns for tenant-private applications.

    Excludes shared, tenant-only infrastructure, and external dependencies.

    Args:
        prefix: Root URL prefix (default: 'api').
        version: API version segment (default: 'v1').

    Returns:
        Tuple of discovered Django URLPattern or URLResolver objects.
    """
    tenant_apps = getattr(settings, "DJANGO_TENANT_PRIVATE_APPS", [])
    excluded = (
        getattr(settings, "SHARED_DJANGO_APPS", [])
        + getattr(settings, "TENANT_ONLY_DJANGO_APPS", [])
        + getattr(settings, "SHARED_EXTRA_DEPENDENCIES", [])
        + getattr(settings, "TENANT_ONLY_EXTRA_DEPENDENCIES", [])
    )
    return _resolve_app_url_entries(
        app_list=tenant_apps,
        excluded_apps=excluded,
        prefix=prefix,
        version=version,
    )


def build_public_app_urlpatterns(
    prefix: str = "api",
    version: str = "v1",
) -> tuple[URLPattern | URLResolver, ...]:
    """
    Construct versioned API URL patterns for public/shared-schema applications.

    Excludes shared, public-only infrastructure, and external dependencies.

    Args:
        prefix: Root URL prefix (default: 'api').
        version: API version segment (default: 'v1').

    Returns:
        Tuple of discovered Django URLPattern or URLResolver objects.
    """
    public_apps = getattr(settings, "DJANGO_TENANT_PUBLIC_APPS", [])
    excluded = (
        getattr(settings, "SHARED_DJANGO_APPS", [])
        + getattr(settings, "PUBLIC_ONLY_DJANGO_APPS", [])
        + getattr(settings, "SHARED_EXTRA_DEPENDENCIES", [])
        + getattr(settings, "PUBLIC_ONLY_EXTRA_DEPENDENCIES", [])
    )
    return _resolve_app_url_entries(
        app_list=public_apps,
        excluded_apps=excluded,
        prefix=prefix,
        version=version,
    )


def build_app_urlpatterns(
    prefix: str = "api",
    version: str = "v1",
) -> tuple[URLPattern | URLResolver, ...]:
    """
    Construct versioned API URL patterns for all configured `PROJECT_APPS`.

    Args:
        prefix: Root URL prefix (default: 'api').
        version: API version segment (default: 'v1').

    Returns:
        Tuple of discovered Django URLPattern or URLResolver objects.
    """
    project_apps = getattr(settings, "PROJECT_APPS", [])
    return _resolve_app_url_entries(
        app_list=project_apps,
        prefix=prefix,
        version=version,
    )
