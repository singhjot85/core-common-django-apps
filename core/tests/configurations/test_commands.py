"""
Unit tests for dev_setup management command, AutoDiscovery, and FileDataSource.
"""

import os
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from core.apps.configurations import app_settings
from core.apps.configurations.management.commands.run_dev_seeders import (
    auto_discover_seeders,
)
from core.seeder.datasource import FileDataSource
from core.seeder.registry import seeder_registry
from core.utils.autodiscovery import AutoDiscovery, AutoDiscoveryError
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


class TestAutoDiscovery:
    """Unit tests for AutoDiscovery and AutoDiscoveryMixin."""

    def test_autodiscovery_scans_and_imports_modules(self):
        discovery = AutoDiscovery(
            root_path=app_settings.DEV_SEEDER_SETUP_PATH,
            scan_all=True,
            scan_depth=4,
            file_name=["seeder.py", "seeders.py"],
        )
        modules = discovery.autodiscover()
        assert isinstance(modules, list)
        assert len(modules) > 0
        module_names = [m.__name__ for m in modules]
        assert "core.setup.crm.seeder" in module_names

    def test_autodiscovery_validation_missing_root_path(self):
        with pytest.raises(AutoDiscoveryError, match="root_path"):
            AutoDiscovery(root_path="", file_name="seeder.py")

    def test_autodiscovery_validation_invalid_hooks(self):
        with pytest.raises(AutoDiscoveryError, match="callable"):
            AutoDiscovery(
                root_path="setup",
                file_name="seeder.py",
                pre_discovery_hooks=["not_a_callable"],
            )

    def test_autodiscovery_lifecycle_hooks(self, settings):
        hook_log = []

        def pre_hook(file_path):
            hook_log.append(f"pre:{file_path.name}")

        def post_hook(file_path, module):
            hook_log.append(f"post:{module.__name__}")

        discovery = AutoDiscovery(
            root_path=os.path.join(settings.CORE_BASE_DIR, "setup/crm"),
            scan_all=False,
            scan_dirs=["."],
            file_name="seeder.py",
            pre_discovery_hooks=[pre_hook],
            post_discovery_hooks=[post_hook],
        )
        discovery.autodiscover()
        assert any("pre:seeder.py" in log for log in hook_log)
        assert any("post:core.setup.crm.seeder" in log for log in hook_log)

    def test_autodiscovery_nonexistent_root_path_raises(self):
        with pytest.raises(AutoDiscoveryError, match="does not exist relative to"):
            AutoDiscovery(root_path="nonexistent/directory/path", file_name="seeder.py")

    def test_autodiscovery_resolve_module_name_outside_base_dir_raises(self):
        discovery = AutoDiscovery(
            root_path="setup",
            file_name="seeder.py",
        )
        with pytest.raises(AutoDiscoveryError, match="not located within"):
            discovery._resolve_module_name(Path("/tmp/outside_module.py"))


class TestFileDataSource:
    """Unit tests for FileDataSource compiled and individual modes."""

    def test_file_data_source_compiled_mode(self, settings):
        ds = FileDataSource(
            os.path.join(
                settings.CORE_BASE_DIR, "setup/crm/dev_customer/customers.json"
            ),
            load_method=FileDataSource.LOAD_COMPILED,
        )
        data = ds.get_data()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "first_name" in data[0]

    def test_file_data_source_individual_directory_mode(self, settings):
        ds = FileDataSource(
            os.path.join(settings.CORE_BASE_DIR, "setup/crm/dev_customer"),
            load_method=FileDataSource.LOAD_INDIVIDUAL,
        )
        data = ds.get_data()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_file_data_source_missing_file_raises(self):
        ds = FileDataSource("non_existent_directory_or_file.json")
        with pytest.raises(FileNotFoundError, match="does not exist relative to"):
            ds.get_data()

    def test_file_data_source_missing_absolute_path_raises(self):
        ds = FileDataSource("/tmp/definitely_not_existing_path_12345.json")
        with pytest.raises(FileNotFoundError, match="absolute path does not exist"):
            ds.get_data()

    def test_core_directories_isolated_from_host_base_dir_override(self, settings):
        """Host project overriding BASE_DIR must not break CORE_BASE_DIR or CORE_APP_DIR data loading."""
        settings.BASE_DIR = Path("/non/existent/host/project/root")
        ds = FileDataSource(
            os.path.join(
                settings.CORE_BASE_DIR, "setup/crm/dev_customer/customers.json"
            )
        )
        data = ds.get_data()
        assert isinstance(data, list)
        assert len(data) > 0


class TestDevSetupCommand:
    """Unit tests for run_dev_seeders management command."""

    def test_run_dev_seeders_raises_in_production(self, settings):
        settings.DEBUG = False
        settings.DJANGO_ENV = "production"

        with pytest.raises(CommandError, match="development environment"):
            call_command("run_dev_seeders")

    def test_run_dev_seeders_executes_in_development(self, settings):
        settings.DEBUG = True
        settings.DJANGO_ENV = "dev"

        out = StringIO()
        with patch("core.seeder.runners.SeedDevelopmentData.run") as mock_run:
            mock_run.return_value = ["dummy_seeded_instance"]
            call_command("run_dev_seeders", stdout=out)
            assert mock_run.called

        output = out.getvalue()
        assert "Successfully completed development setup" in output

    def test_auto_discover_seeders_registers_seeders(self):
        auto_discover_seeders()
        registry = seeder_registry.registry
        assert "dev_customer_seeder" in registry
        assert "dev_user_seeder" in registry
