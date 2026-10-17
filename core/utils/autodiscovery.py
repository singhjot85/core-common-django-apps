import importlib
from functools import cached_property
from pathlib import Path


class AutoDiscoveryError(Exception):
    """Custom exception for errors related to the AutoDiscovery class."""

    pass


class AutoDiscoveryMixin:

    AUTO_DISCOVERY_SETTINGS = {
        "root_path",  # Root directory to start scanning for modules
        "scan_all",  # Whether to scan all subdirectories or only specified ones
        "scan_dirs",  # List of specific directories to scan for modules
        "scan_depth",  # Depth of scanning for modules in subdirectories
        "file_name",  # Name of the file to look for in the specified directories
        "pre_discovery_hooks",  # List of callable functions to execute before the discovery process
        "post_discovery_hooks",  # List of callable functions to execute after the discovery process
    }

    def __init__(self, *args, **kwargs):
        for attr in self.AUTO_DISCOVERY_SETTINGS:
            value = kwargs.get(attr, self.default_configuration.get(attr, None))

            setattr(self, attr, value)

            if (validator := getattr(self, f"_validate_{attr}", None)) and callable(
                validator
            ):
                validator(value)

        self.normalize_settings()
        self.validate()

    @cached_property
    def default_configuration(self):
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
        scan_all = getattr(self, "scan_all", False)
        if scan_all:
            setattr(self, "scan_dirs", [])

        scan_all = getattr(self, "scan_all", False)
        if scan_all:
            setattr(self, "scan_dirs", [])
            if not getattr(self, "scan_depth", None):
                setattr(
                    self, "scan_depth", 1
                )  # Default scan depth to 1 if not provided when scan_all is True

    def validate(self):
        scan_dirs = getattr(self, "scan_dirs", [])
        scan_depth = getattr(self, "scan_depth")
        if scan_dirs is None and scan_depth is None:
            raise AutoDiscoveryError("scan_depth must be None when scan_dirs is None.")

    def _validate_file_name(self):
        file_name = getattr(self, "file_name", None)
        if not file_name or not isinstance(file_name, str):
            raise AutoDiscoveryError("file_name must be a non-empty string.")

    def _validate_pre_discovery_hooks(self):
        pre_discovery_hooks = getattr(self, "pre_discovery_hooks", [])
        if not isinstance(pre_discovery_hooks, list) or not all(
            callable(hook) for hook in pre_discovery_hooks
        ):
            raise AutoDiscoveryError(
                "pre_discovery_hooks must be a list of callable functions."
            )

    def _validate_post_discovery_hooks(self):
        post_discovery_hooks = getattr(self, "post_discovery_hooks", [])
        if not isinstance(post_discovery_hooks, list) or not all(
            callable(hook) for hook in post_discovery_hooks
        ):
            raise AutoDiscoveryError(
                "post_discovery_hooks must be a list of callable functions."
            )

    def _validate_root_path(self):
        root_path = getattr(self, "root_path", None)
        if not root_path:
            raise AutoDiscoveryError("root_path must be provided and cannot be empty.")

    def _scan_all_dirs(self, root_path: Path, scan_depth: int = 0):
        scan_depth = getattr(self, "scan_depth")

        depth = 0
        for content in root_path.iterdir():
            depth += 1
            if content.is_dir() and depth <= scan_depth:
                # Conditional recursive call
                self._scan_all_dirs(content)

            if content.is_file() and str(content.absolute()).endswith(".py"):
                self.process_file(content)

    def _scan_directories(self, root_path, scan_dirs):

        for dir in scan_dirs:
            curent_dir = root_path + dir
            self.process_file(curent_dir)

    def process_file(self, file: Path):
        file_name = getattr(self, "file_name")

        if file_name != file.name:
            return

        pre_discovery_hooks = getattr(self, "pre_discovery_hooks")
        for hook in pre_discovery_hooks:
            hook(file)

        try:
            importlib.import_module(file.parts, file_name)
        except Exception as e:
            raise AutoDiscoveryError(f"Error importing file: {file_name}") from e

        post_discovery_hooks = getattr(self, "post_discovery_hooks")
        for hook in post_discovery_hooks:
            hook(file)

    def autodiscover(self):
        root_path = getattr(self, "root_path")

        path = Path(root_path)
        if getattr(self, "scan_all", False):
            self._scan_all_dirs(path)
        elif scan_dirs := getattr(self, "scan_dirs"):
            self._scan_directories(path, scan_dirs)
