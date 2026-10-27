"""
Data source abstractions for the database seeder framework.

Defines pluggable data sources (such as JSON files, directories of JSON objects,
or factories) that supply seed records to BaseSeeder instances.
"""

from __future__ import annotations

import abc
import json
import logging
import typing
from enum import Enum
from pathlib import Path

from django.conf import settings

LOGGER = logging.getLogger(__name__)


class DataSourceType(Enum):
    """Enumeration representing supported data source categories."""

    JSON_FILE = "json_file"
    FACTORIES = "factories"


class AbstractDataSource(abc.ABC):
    """
    Abstract base class for all seeder data sources.

    Subclasses must implement `get_data()` to yield a list or dictionary
    of records formatted for consumption by a BaseSeeder.
    """

    source_type: str

    @abc.abstractmethod
    def get_data(self) -> typing.Union[list, dict]:
        """
        Retrieve and parse seed records from the underlying data source.

        Returns:
            list | dict: Extracted data records ready for seeder processing.
        """
        pass


class FileDataSource(AbstractDataSource):
    """
    File-based data source supporting single-file and multi-file directory layouts.

    Modes:
    - `LOAD_COMPILED ("compile")`: Reads an entire collection of objects from a single JSON file
      containing a JSON array.
    - `LOAD_INDIVIDUAL ("individual")`: Scans a directory for multiple individual `*.json` files,
      where each file represents a single object or a subset of objects.
    """

    file_path: str
    load_method: str

    LOAD_COMPILED = "compile"
    LOAD_INDIVIDUAL = "individual"

    def __init__(
        self,
        path: typing.Union[str, Path],
        load_method: typing.Optional[str] = None,
    ):
        """
        Initialize the file data source.

        Args:
            path (str | Path): Path to a JSON file (compiled mode) or directory (individual mode).
            load_method (str, optional): `LOAD_COMPILED` or `LOAD_INDIVIDUAL`. If omitted,
                it is automatically inferred based on whether the resolved path is a file or directory.
        """
        self.source_type = DataSourceType.JSON_FILE.value
        self.file_path = str(path)
        self.load_method = load_method or self.LOAD_COMPILED

    def _resolve_path(self) -> Path:
        """
        Resolve the file or directory path relative to settings.CORE_BASE_DIR,
        settings.BASE_DIR, or as an absolute path.

        Returns:
            Path: Resolved filesystem Path object.

        Raises:
            FileNotFoundError: If the path does not exist.
        """
        path = Path(self.file_path)
        if path.is_absolute():
            if path.exists():
                return path
            raise FileNotFoundError(
                f"FileDataSource absolute path does not exist: {path}"
            )

        core_base = getattr(settings, "CORE_BASE_DIR", None)
        base_dir = getattr(settings, "BASE_DIR", None)

        if core_base:
            resolved_core = Path(core_base) / path
            if resolved_core.exists():
                return resolved_core

        if base_dir:
            resolved_base = Path(base_dir) / path
            if resolved_base.exists():
                return resolved_base

        raise FileNotFoundError(
            f"FileDataSource path does not exist relative to CORE_BASE_DIR ({core_base}) "
            f"or BASE_DIR ({base_dir}): original '{self.file_path}'"
        )

    def get_data(self) -> list:
        """
        Read and return data from the specified JSON file or directory.

        Returns:
            list: Parsed list of records to be seeded.

        Raises:
            FileNotFoundError: If the specified file or directory cannot be found.
            ValueError: If JSON data fails structural validation.
        """
        resolved_path = self._resolve_path()

        if not resolved_path.exists():
            raise FileNotFoundError(
                f"FileDataSource path does not exist: {resolved_path} (original: {self.file_path})"
            )

        # Inferred mode handling
        is_directory = resolved_path.is_dir()
        use_individual = self.load_method == self.LOAD_INDIVIDUAL or (
            is_directory and self.load_method != self.LOAD_COMPILED
        )

        if not use_individual:
            # Compiled mode: single JSON file
            with open(resolved_path, "r", encoding="utf-8") as file:
                compiled_data = json.load(file)

            if isinstance(compiled_data, dict):
                return [compiled_data]
            elif isinstance(compiled_data, list):
                return compiled_data
            else:
                raise ValueError(
                    f"Data in JSON file {resolved_path} must be a list of items or single dictionary."
                )

        # Individual mode: directory containing individual JSON files
        compiled_data = []
        json_files = sorted(resolved_path.glob("*.json"))

        for file in json_files:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict):
                compiled_data.append(data)
            elif isinstance(data, list):
                compiled_data.extend(data)
            else:
                raise ValueError(
                    f"Data in JSON file {file} must be a dictionary or list."
                )

        return compiled_data
