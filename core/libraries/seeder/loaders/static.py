"""
Static and file-based loaders for seeder framework.
"""

from __future__ import annotations

import json
import logging
import pathlib
import typing

from django.conf import settings

from core.libraries.seeder.exceptions import SeederDataLoaderException
from core.libraries.seeder.loaders.base import BaseFileDataSource

if typing.TYPE_CHECKING:
    from factory.django import DjangoModelFactory

LOGGER = logging.getLogger(__name__)


class FileBasedLoader(BaseFileDataSource):
    """File-based data loader resolving JSON records from configured paths."""

    loader_type: str = "file_loader"

    def resolve_search_directories(self) -> list[pathlib.Path]:
        """
        Resolve data directories across host project and core framework.

        Priority order:
        1. settings.SETUP_DIR
        2. settings.BASE_DIR
        3. settings.CORE_SETUP_DIR
        4. settings.CORE_BASE_DIR

        Never searches app dirs. Collects existing paths from both host repo
        (SETUP_DIR / BASE_DIR) and core framework (CORE_SETUP_DIR / CORE_BASE_DIR)
        to seed both core fixtures and host project overrides.
        """
        candidate = pathlib.Path(self.dir_name)
        if candidate.is_absolute() and candidate.exists():
            return [candidate]

        search_roots = [
            getattr(settings, "SETUP_DIR", None),
            getattr(settings, "BASE_DIR", None),
            getattr(settings, "CORE_SETUP_DIR", None),
            getattr(settings, "CORE_BASE_DIR", None),
        ]

        resolved_paths: list[pathlib.Path] = []
        seen: set[str] = set()

        for root in search_roots:
            if not root:
                continue
            resolved = pathlib.Path(root) / self.dir_name
            if resolved.exists():
                canonical = str(resolved.resolve())
                if canonical not in seen:
                    seen.add(canonical)
                    resolved_paths.append(resolved)

        return resolved_paths

    def load_files(self, target_path: pathlib.Path) -> list[pathlib.Path]:
        """
        Discover file or directory of files to read.

        If target_path is a file, returns a single-item list.
        If target_path is a directory, returns sorted *.json files.
        """
        if not target_path.exists():
            return []

        if target_path.is_file():
            return [target_path]

        return sorted(target_path.glob("*.json"))

    def load(self, file: pathlib.Path) -> typing.Any:
        """Read and parse JSON from the given file."""
        return json.loads(file.read_text(encoding="utf-8"))

    def get_data(self) -> list[dict]:
        """
        Retrieve all records as a flat list of dictionaries.

        Collects records across both host project and core setup directories,
        flattening compiled JSON lists and aggregating individual JSON files.
        """
        search_dirs = self.resolve_search_directories()
        if not search_dirs:
            LOGGER.warning(
                "Data path '%s' configured for seeder could not be resolved in SETUP_DIR or CORE_SETUP_DIR.",
                self.dir_name,
            )
            return []

        compiled_data: list[dict] = []
        for target_path in search_dirs:
            files = self.load_files(target_path)
            for file in files:
                try:
                    data = self.load(file)
                    validated = self.validate_data(data, file)
                    if validated is None:
                        continue

                    if isinstance(validated, list):
                        compiled_data.extend(validated)
                    elif isinstance(validated, dict):
                        compiled_data.append(validated)
                except Exception as exc:
                    LOGGER.error("Failed to load seeder file: %s", file, exc_info=exc)
                    raise SeederDataLoaderException(self.loader_type, str(exc)) from exc

        return compiled_data


class FactoryBasedLoader(FileBasedLoader):
    """Loader integrating factory-boy factories for generating dynamic mock data."""

    loader_type: str = "factory_loader"
    factory: type[DjangoModelFactory]

    def __init__(
        self,
        factory: type[DjangoModelFactory],
        directory_name: str,
        load_method: str | None = None,
    ) -> None:
        self.factory = factory
        super().__init__(directory_name=directory_name, load_method=load_method)
