"""
Base abstractions for seeder data sources.
"""

from __future__ import annotations

import abc
import logging
import typing

if typing.TYPE_CHECKING:
    import pathlib

LOGGER = logging.getLogger(__name__)


class AbstractDataSource(abc.ABC):
    """
    Abstract base class for all seeder data sources.

    Subclasses must implement `get_data()` to return a collection of records.
    """

    loader_type: str

    @abc.abstractmethod
    def get_data(self) -> list[dict] | dict:
        """
        Retrieve and parse seed records from the underlying data source.

        Returns:
            list[dict] | dict: Extracted data records ready for seeder processing.
        """
        pass


class BaseFileDataSource(AbstractDataSource):
    """
    Abstract base class for file-based seeder data sources.

    Modes:
        - LOAD_COMPILED ("compile"): Reads a JSON array from a single file.
        - LOAD_INDIVIDUAL ("individual"): Reads multiple JSON records from a directory of files.
    """

    LOAD_COMPILED = "compile"
    LOAD_INDIVIDUAL = "individual"

    dir_name: str
    load_method: str

    def __init__(
        self,
        directory_name: str,
        load_method: str | None = None,
    ) -> None:
        self.dir_name = directory_name
        self.load_method = load_method or self.LOAD_COMPILED

    def validate_data(
        self, data: typing.Any, file: pathlib.Path
    ) -> list[dict] | dict | None:
        """
        Validate parsed JSON data against expected structure.

        Args:
            data: Parsed Python data structure from file.
            file: Path to the source file.

        Returns:
            Validated data structure, or None if invalid.
        """
        if not data:
            LOGGER.warning("No data found in file: %s", file)
            return None

        if isinstance(data, dict):
            return data

        if isinstance(data, list):
            return data

        LOGGER.error("Invalid data format in file: %s; dropping file.", file)
        return None

    def load(self, file: pathlib.Path) -> typing.Any:
        """Parse raw file contents into Python datatypes."""
        raise NotImplementedError

    def load_files(self, target_path: pathlib.Path) -> list[pathlib.Path]:
        """Discover files to process based on path and load method."""
        raise NotImplementedError
