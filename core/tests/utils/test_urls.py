"""
Tests for URL pattern auto-discovery and path building in `core.utils.urls`.
"""

from unittest.mock import patch

from django.urls import URLPattern, URLResolver

from core.utils.urls import (
    _build_url_path,
    _has_urls_module,
    _resolve_app_url_entries,
    build_app_urlpatterns,
    build_public_app_urlpatterns,
    build_tenant_app_urlpatterns,
)


class TestURLUtils:
    """Test suite for URL utility functions."""

    def test_build_url_path_defaults(self):
        """Test default prefix ('api') and version ('v1')."""
        path = _build_url_path("users")
        assert path == "api/users/v1/"

    def test_build_url_path_custom_prefix_and_version(self):
        """Test custom prefix and version with varied slash stripping."""
        path = _build_url_path("crm", prefix="/custom_api/", version="/v2/")
        assert path == "custom_api/crm/v2/"

    def test_build_url_path_empty_prefix(self):
        """Test building URL path when prefix is empty."""
        path = _build_url_path("invoices", prefix="", version="v1")
        assert path == "invoices/v1/"

    def test_has_urls_module_existing(self):
        """Verify _has_urls_module returns True for known app with urls.py."""
        assert _has_urls_module("core.apps.users") is True
        assert _has_urls_module("core.apps.crm") is True

    def test_has_urls_module_non_existing(self):
        """Verify _has_urls_module returns False for non-existing or missing module."""
        assert _has_urls_module("core.apps.configurations") is False
        assert _has_urls_module("non.existent.app") is False

    def test_resolve_app_url_entries_filters_and_excludes(self):
        """Verify exclusion and skipping of apps without URLs module."""
        apps = ["core.apps.users", "core.apps.crm", "core.apps.configurations"]
        excluded = ["core.apps.crm"]

        entries = _resolve_app_url_entries(
            app_list=apps,
            excluded_apps=excluded,
            prefix="api",
            version="v1",
        )

        assert isinstance(entries, tuple)
        # crm is excluded, configurations has no urls.py -> only users remains
        assert len(entries) == 1
        assert isinstance(entries[0], (URLPattern, URLResolver))
        assert str(entries[0].pattern) == "api/users/v1/"

    def test_build_tenant_app_urlpatterns(self):
        """Verify build_tenant_app_urlpatterns returns valid URLPattern or URLResolver tuple."""
        entries = build_tenant_app_urlpatterns()
        assert isinstance(entries, tuple)
        for entry in entries:
            assert isinstance(entry, (URLPattern, URLResolver))

        # Check expected tenant private apps with URLs are included
        patterns = [str(entry.pattern) for entry in entries]
        assert "api/users/v1/" in patterns
        assert "api/crm/v1/" in patterns
        assert "api/invoices/v1/" in patterns

    def test_build_public_app_urlpatterns(self):
        """Verify build_public_app_urlpatterns returns valid URLPattern or URLResolver tuple."""
        entries = build_public_app_urlpatterns()
        assert isinstance(entries, tuple)
        for entry in entries:
            assert isinstance(entry, (URLPattern, URLResolver))

        patterns = [str(entry.pattern) for entry in entries]
        assert "api/users/v1/" in patterns
        assert "api/tenants/v1/" in patterns

    def test_build_app_urlpatterns(self):
        """Verify build_app_urlpatterns iterates PROJECT_APPS."""
        with patch("core.utils.urls.settings.PROJECT_APPS", ["core.apps.users"]):
            entries = build_app_urlpatterns(prefix="v1", version="")
            assert len(entries) == 1
            assert str(entries[0].pattern) == "v1/users/"
