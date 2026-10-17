from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from core.apps.configurations.management.commands.dev_setup import (
    auto_discover_seeders,
    load_seed_data,
)
from core.seeder.registry import seeder_registry
from core.utils.checks import is_development, is_production


class TestEnvironmentChecks:
    """Verify is_development and is_production checks."""

    def test_is_development_in_dev_env(self, settings):
        settings.DEBUG = True
        settings.DJANGO_ENV = "dev"
        assert is_development() is True
        assert is_production() is False

    def test_is_development_in_prod_env(self, settings):
        settings.DEBUG = False
        settings.DJANGO_ENV = "production"
        assert is_development() is False
        assert is_production() is True


class TestDevSetupCommand:
    """Unit tests for dev_setup management command."""

    def test_dev_setup_raises_in_production(self, settings):
        settings.DEBUG = False
        settings.DJANGO_ENV = "production"

        with pytest.raises(CommandError, match="development environment"):
            call_command("dev_setup")

    def test_dev_setup_executes_in_development(self, settings):
        settings.DEBUG = True
        settings.DJANGO_ENV = "dev"

        out = StringIO()
        with patch("core.seeder.runners.SeedData.run") as mock_run:
            call_command("dev_setup", stdout=out)
            assert mock_run.called

        output = out.getvalue()
        assert "Successfully completed development setup" in output

    def test_seed_data_alias_executes_in_development(self, settings):
        settings.DEBUG = True
        settings.DJANGO_ENV = "dev"

        out = StringIO()
        with patch("core.seeder.runners.SeedData.run") as mock_run:
            call_command("seed_data", stdout=out)
            assert mock_run.called

        output = out.getvalue()
        assert "Successfully completed development setup" in output

    def test_auto_discover_seeders_registers_seeders(self):
        auto_discover_seeders()
        registry = seeder_registry.registry
        assert "dev_customer_seeder" in registry
        assert "configuration_seeder" in registry

    def test_load_seed_data_returns_fixture_dict(self):
        seed_data = load_seed_data()
        assert isinstance(seed_data, dict)
        assert len(seed_data) > 0
        assert "configuration" in seed_data or "configuration_seeder" in seed_data
        assert "dev_customer" in seed_data or "dev_customer_seeder" in seed_data
