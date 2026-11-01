"""
Tests for URL pattern resolution and explicit route building in `core.utils.urls`.
"""

import pytest
from django.urls import URLResolver, resolve, reverse

import core.config.public_urls
import core.config.urls
from core.config.api_protected import core_api_url_patterns, core_url_mapping
from core.utils.urls import resolve_and_build_paths


class TestResolveAndBuildPaths:
    """Test suite for `resolve_and_build_paths` utility."""

    def test_resolve_and_build_paths_defaults(self):
        """Test default prefix ('api') and version ('v1')."""
        mapping = [("core.apps.users.urls", "v1", "users")]
        resolvers = resolve_and_build_paths(mapping)

        assert len(resolvers) == 1
        assert isinstance(resolvers[0], URLResolver)
        assert str(resolvers[0].pattern) == "api/users/v1/"

    def test_resolve_and_build_paths_custom_prefix(self):
        """Test custom prefix and None/empty prefix."""
        mapping = [("core.apps.users.urls", "v1", "users")]

        custom_prefix = resolve_and_build_paths(mapping, prefix="custom")
        assert str(custom_prefix[0].pattern) == "custom/users/v1/"

        no_prefix = resolve_and_build_paths(mapping, prefix=None)
        assert str(no_prefix[0].pattern) == "users/v1/"

        empty_prefix = resolve_and_build_paths(mapping, prefix="")
        assert str(empty_prefix[0].pattern) == "users/v1/"

    def test_resolve_and_build_paths_omitted_or_none_version(self):
        """Test that None or empty version defaults to 'v1'."""
        mapping = [
            ("core.apps.users.urls", None, "users"),
            ("core.apps.crm.urls", "", "customers"),
        ]
        resolvers = resolve_and_build_paths(mapping)

        assert str(resolvers[0].pattern) == "api/users/v1/"
        assert str(resolvers[1].pattern) == "api/customers/v1/"

    def test_resolve_and_build_paths_2_tuple(self):
        """Test 2-tuple entry (file_path, api_path) defaults version to 'v1'."""
        mapping = [("core.apps.users.urls", "users")]
        resolvers = resolve_and_build_paths(mapping)

        assert len(resolvers) == 1
        assert str(resolvers[0].pattern) == "api/users/v1/"

    def test_resolve_and_build_paths_slash_normalization(self):
        """Test normalization of leading and trailing slashes in components."""
        mapping = [("core.apps.users.urls", "/v2/", "/users/")]
        resolvers = resolve_and_build_paths(mapping, prefix="/api/")

        assert str(resolvers[0].pattern) == "api/users/v2/"

    def test_resolve_and_build_paths_invalid_tuple_raises_value_error(self):
        """Test that invalid tuple lengths raise ValueError."""
        with pytest.raises(ValueError, match="Invalid URL mapping entry, got:"):
            resolve_and_build_paths([("invalid_single_entry",)])

        with pytest.raises(ValueError, match="Invalid URL mapping entry, got:"):
            resolve_and_build_paths([("a", "b", "c", "d")])

    def test_resolve_and_build_paths_multiple_entries(self):
        """Test building paths for multiple mappings."""
        mapping = [
            ("core.apps.users.urls", "v1", "users"),
            ("core.apps.crm.urls", "v1", "customers"),
        ]
        resolvers = resolve_and_build_paths(mapping)

        assert len(resolvers) == 2
        patterns = [str(r.pattern) for r in resolvers]
        assert "api/users/v1/" in patterns
        assert "api/customers/v1/" in patterns


class TestCoreAPIURLConfiguration:
    """Test suite for core API URL wiring and reverse lookup."""

    def test_core_url_mapping_and_patterns_defined(self):
        """Verify core_url_mapping contains expected registered apps."""
        registered_apps = [entry[0] for entry in core_url_mapping]
        assert "core.apps.users.urls" in registered_apps
        assert "core.apps.crm.urls" in registered_apps

        patterns = [str(r.pattern) for r in core_api_url_patterns]
        assert "api/users/v1/" in patterns
        assert "api/customers/v1/" in patterns

    def test_reverse_known_endpoint(self):
        """Verify known endpoint can be reversed through core URL patterns."""
        reversed_url = reverse("social-google-login")
        assert reversed_url == "/api/users/v1/auth/social/google/"

    def test_resolve_known_endpoint(self):
        """Verify known URL path resolves to expected view name."""
        match = resolve("/api/users/v1/auth/social/google/")
        assert match.url_name == "social-google-login"

    def test_urls_and_public_urls_importable(self):
        """Verify root urlconfs can be imported without error."""
        assert len(core.config.urls.urlpatterns) > 0
        assert len(core.config.public_urls.urlpatterns) > 0
