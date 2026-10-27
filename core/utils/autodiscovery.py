"""
Autodiscovery utility for dynamic module scanning and loading.

Provides configurable directory scanning, file-matching filters, pre- and post-discovery
lifecycle hooks, and automated Python module import resolution.
"""

from __future__ import annotations

import importlib
import logging
import typing
from functools import cached_property
from pathlib import Path

from django.conf import settings

LOGGER = logging.getLogger(__name__)


class AutoDiscoveryError(Exception):
    """Custom exception for errors encountered during the AutoDiscovery process."""

    pass


class AutoDiscoveryMixin:
    """
    Mixin providing declarative autodiscovery capabilities.

    Scans directories recursively or through specified directory lists to locate
    and import target Python files (such as seeder definitions or registry hooks).
    """

    AUTO_DISCOVERY_SETTINGS = {
        "root_path",  # Root directory to start scanning for modules
        "scan_all",  # Whether to scan all subdirectories or only specified ones
        "scan_dirs",  # List of specific directories to scan for modules
        "scan_depth",  # Depth of scanning for modules in subdirectories
        "file_name",  # Name or list of names of files to look for
        "pre_discovery_hooks",  # Callables to execute before a module is imported
        "post_discovery_hooks",  # Callables to execute after a module is imported
    }

    root_path: typing.Union[str, Path]
    scan_all: bool
    scan_dirs: list[str]
    scan_depth: int
    file_name: typing.Union[str, list[str], tuple[str, ...], set[str]]
    pre_discovery_hooks: list[typing.Callable]
    post_discovery_hooks: list[typing.Callable]
    discovered_modules: list

    def __init__(self, *args, **kwargs):
        """
        Initialize autodiscovery settings from keyword arguments or defaults.

        Args:
            *args: Positional arguments.
            **kwargs: Configuration overrides for any setting in AUTO_DISCOVERY_SETTINGS.
        """
        self.discovered_modules = []

        for attr in self.AUTO_DISCOVERY_SETTINGS:
            value = kwargs.get(attr, self.default_configuration.get(attr, None))
            setattr(self, attr, value)

        self.normalize_settings()
        self.validate()

    @cached_property
    def default_configuration(self) -> dict:
        """
        Default configuration dictionary for autodiscovery.

        Returns:
            dict: Default parameter mapping.
        """
        return {
            "root_path": "",
            "scan_all": False,
            "scan_dirs": [],
            "scan_depth": 1,
            "file_name": "",
            "pre_discovery_hooks": [],
            "post_discovery_hooks": [],
        }

    def normalize_settings(self):
        """
        Normalize and sanitize configuration values before validation and execution.
        """
        scan_all = getattr(self, "scan_all", False)
        if scan_all:
            setattr(self, "scan_dirs", [])
            if not getattr(self, "scan_depth", None):
                setattr(self, "scan_depth", 1)

        # Convert root_path to Path object if provided as string
        root_path = getattr(self, "root_path", "")
        if root_path:
            path_obj = Path(root_path)
            if not path_obj.is_absolute():
                core_base = getattr(settings, "CORE_BASE_DIR", None)
                base_dir = getattr(settings, "BASE_DIR", None)

                resolved = None
                if core_base and (Path(core_base) / path_obj).exists():
                    resolved = Path(core_base) / path_obj
                elif base_dir and (Path(base_dir) / path_obj).exists():
                    resolved = Path(base_dir) / path_obj
                elif core_base:
                    resolved = Path(core_base) / path_obj
                elif base_dir:
                    resolved = Path(base_dir) / path_obj
                else:
                    raise AutoDiscoveryError(
                        f"Cannot resolve relative root_path '{root_path}': neither CORE_BASE_DIR nor BASE_DIR is configured."
                    )
                path_obj = resolved

            setattr(self, "root_path", path_obj)

    def validate(self):
        """
        Validate configured autodiscovery settings.

        Raises:
            AutoDiscoveryError: If any setting fails validation.
        """
        self._validate_root_path()
        self._validate_file_name()
        self._validate_pre_discovery_hooks()
        self._validate_post_discovery_hooks()

        scan_dirs = getattr(self, "scan_dirs", [])
        scan_depth = getattr(self, "scan_depth", None)
        if scan_dirs is None and scan_depth is None:
            raise AutoDiscoveryError("scan_depth must be None when scan_dirs is None.")

    def _validate_file_name(self, value=None):
        """Validate that file_name is a non-empty string or collection of strings."""
        file_name = value if value is not None else getattr(self, "file_name", None)
        if not file_name:
            raise AutoDiscoveryError(
                "file_name must be a non-empty string or collection of strings."
            )
        if isinstance(file_name, (list, tuple, set)):
            if not all(isinstance(f, str) and f for f in file_name):
                raise AutoDiscoveryError(
                    "All items in file_name collection must be non-empty strings."
                )
        elif not isinstance(file_name, str):
            raise AutoDiscoveryError(
                "file_name must be a non-empty string or collection of strings."
            )

    def _validate_pre_discovery_hooks(self, value=None):
        """Validate that pre_discovery_hooks is a list of callables."""
        hooks = value if value is not None else getattr(self, "pre_discovery_hooks", [])
        if not isinstance(hooks, list) or not all(callable(hook) for hook in hooks):
            raise AutoDiscoveryError(
                "pre_discovery_hooks must be a list of callable functions."
            )

    def _validate_post_discovery_hooks(self, value=None):
        """Validate that post_discovery_hooks is a list of callables."""
        hooks = (
            value if value is not None else getattr(self, "post_discovery_hooks", [])
        )
        if not isinstance(hooks, list) or not all(callable(hook) for hook in hooks):
            raise AutoDiscoveryError(
                "post_discovery_hooks must be a list of callable functions."
            )

    def _validate_root_path(self, value=None):
        """Validate that root_path is provided and exists."""
        root_path = value if value is not None else getattr(self, "root_path", None)
        if not root_path:
            raise AutoDiscoveryError("root_path must be provided and cannot be empty.")

        path_obj = Path(root_path)
        if not path_obj.is_absolute():
            core_base = getattr(settings, "CORE_BASE_DIR", None)
            base_dir = getattr(settings, "BASE_DIR", None)

            resolved = None
            if core_base and (Path(core_base) / path_obj).exists():
                resolved = Path(core_base) / path_obj
            elif base_dir and (Path(base_dir) / path_obj).exists():
                resolved = Path(base_dir) / path_obj
            elif core_base:
                resolved = Path(core_base) / path_obj
            elif base_dir:
                resolved = Path(base_dir) / path_obj
            else:
                raise AutoDiscoveryError(
                    f"Cannot resolve relative root_path '{root_path}': neither CORE_BASE_DIR nor BASE_DIR is configured."
                )
            path_obj = resolved

        if not path_obj.exists():
            core_base = getattr(settings, "CORE_BASE_DIR", None)
            base_dir = getattr(settings, "BASE_DIR", None)
            raise AutoDiscoveryError(
                f"root_path '{root_path}' does not exist relative to CORE_BASE_DIR ({core_base}) or BASE_DIR ({base_dir}): {path_obj}"
            )

    def _resolve_module_name(self, file: Path) -> str:
        """
        Convert a Python file path into a valid dotted import module name.

        Args:
            file (Path): Absolute or relative path to the Python file.

        Returns:
            str: Dotted Python module name suitable for importlib.import_module.

        Raises:
            AutoDiscoveryError: If module cannot be resolved.
        """
        file_resolved = file.resolve()

        core_base = getattr(settings, "CORE_BASE_DIR", None)
        if core_base:
            core_path = Path(core_base).resolve()
            try:
                rel = file_resolved.relative_to(core_path)
                return f"{core_path.name}.{'.'.join(rel.with_suffix('').parts)}"
            except ValueError:
                pass

        base_dir = getattr(settings, "BASE_DIR", None)
        if base_dir:
            base_path = Path(base_dir).resolve()
            try:
                rel = file_resolved.relative_to(base_path)
                return ".".join(rel.with_suffix("").parts)
            except ValueError:
                pass

        raise AutoDiscoveryError(
            f"Module file '{file_resolved}' is not located within CORE_BASE_DIR '{core_base}' or BASE_DIR '{base_dir}'."
        )

    def _scan_all_dirs(self, root_path: Path, current_depth: int = 1):
        """
        Recursively scan all subdirectories down to configured scan_depth.

        Args:
            root_path (Path): Current directory being traversed.
            current_depth (int): Current depth in directory hierarchy.
        """
        max_depth = getattr(self, "scan_depth", 1) or 1
        if not root_path.exists() or not root_path.is_dir():
            return

        for content in root_path.iterdir():
            if content.is_file() and content.suffix == ".py":
                self.process_file(content)
            elif content.is_dir() and current_depth < max_depth:
                self._scan_all_dirs(content, current_depth=current_depth + 1)

    def _scan_directories(self, root_path: Path, scan_dirs: list[str]):
        """
        Scan only explicitly targeted subdirectories under root_path.

        Args:
            root_path (Path): Base directory.
            scan_dirs (list[str]): List of directory names or relative paths.
        """
        for d in scan_dirs:
            target = root_path / d if not Path(d).is_absolute() else Path(d)
            if target.is_dir():
                for content in target.iterdir():
                    if content.is_file() and content.suffix == ".py":
                        self.process_file(content)
            elif target.is_file() and target.suffix == ".py":
                self.process_file(target)

    def process_file(self, file: Path):
        """
        Process a candidate file, verifying filename match, running lifecycle hooks,
        and importing the module.

        Args:
            file (Path): Path to candidate file.

        Raises:
            AutoDiscoveryError: If module import fails.
        """
        file_name = getattr(self, "file_name")
        allowed_names = (
            file_name if isinstance(file_name, (list, tuple, set)) else [file_name]
        )

        if file.name not in allowed_names:
            return

        # Execute pre-discovery hooks
        pre_discovery_hooks = getattr(self, "pre_discovery_hooks", [])
        for hook in pre_discovery_hooks:
            hook(file)

        # Import target Python module
        mod_name = self._resolve_module_name(file)
        try:
            module = importlib.import_module(mod_name)
            self.discovered_modules.append(module)
            LOGGER.debug("AutoDiscovered and imported: %s", mod_name)
        except Exception as e:
            raise AutoDiscoveryError(
                f"Error importing file: {file} as module '{mod_name}'"
            ) from e

        # Execute post-discovery hooks
        post_discovery_hooks = getattr(self, "post_discovery_hooks", [])
        for hook in post_discovery_hooks:
            hook(file, module)

    def autodiscover(self) -> list:
        """
        Execute directory scanning and module discovery according to settings.

        Returns:
            list: List of imported module objects.
        """
        root_path = getattr(self, "root_path")
        path = Path(root_path)

        if getattr(self, "scan_all", False):
            self._scan_all_dirs(path)
        elif scan_dirs := getattr(self, "scan_dirs", []):
            self._scan_directories(path, scan_dirs)

        return self.discovered_modules


class AutoDiscovery(AutoDiscoveryMixin):
    """
    Concrete AutoDiscovery runner class.

    Example:
    >>> discovery = AutoDiscovery(
    ...     root_path="core/setup",
    ...     scan_all=True,
    ...     scan_depth=3,
    ...     file_name=["seeder.py", "seeders.py"],
    ... )
    >>> discovered = discovery.autodiscover()
    """

    pass
