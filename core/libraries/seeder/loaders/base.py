import abc
import logging
import typing

LOGGER = logging.getLogger(__name__)
if typing.TYPE_CHECKING:
    import pathlib


class AbstractDataSource(abc.ABC):
    """
    Abstract base class for all seeder data sources.

    Subclasses must implement `get_data()` to yield a list or dictionary
    of records formatted for consumption by a BaseSeeder.
    """

    loader_type: str

    @abc.abstractmethod
    def get_data(self) -> typing.Union[list, dict]:
        """
        Retrieve and parse seed records from the underlying data source.

        Returns:
            list | dict: Extracted data records ready for seeder processing.
        """
        pass


class BaseFileDataSource(AbstractDataSource):
    """
    File-based data source supporting
    - single-file and multi-file directory layouts.
    - host project override capabilities.

    Modes:
    - `LOAD_COMPILED ("compile")`: Reads an entire collection of objects from a single JSON file
        containing a JSON array.
    - `LOAD_INDIVIDUAL ("individual")`: Scans a directory for multiple individual `*.json` files,
        where each file represents a single object or a subset of objects.
    """

    if typing.TYPE_CHECKING:
        file_path: str
        load_method: str

    LOAD_COMPILED = "compile"
    LOAD_INDIVIDUAL = "individual"

    def __init__(
        self,
        directory_name: str,
        load_method: typing.Optional[str] = None,
    ):
        """
        Initialize the file data source.

        Args:
            path (str | Path): Path to a JSON file (compiled mode) or directory (individual mode).
            load_method (str, optional): `LOAD_COMPILED` or `LOAD_INDIVIDUAL`. If omitted,
                it is automatically inferred based on whether the resolved path is a file or directory.
        """
        self.load_method = load_method or self.LOAD_COMPILED
        self.dir_name = directory_name

    def validate_data(self, data, file: "pathlib.Path"):
        """ """
        if not data:
            LOGGER.warning(f"No data found in file {file}")

        if isinstance(data, dict) and self.load_method == self.LOAD_INDIVIDUAL:
            return data

        if isinstance(data, list) and self.load_method == self.LOAD_COMPILED:
            return data

        LOGGER.error(f"Invalid data in file: {file}, dropping file from seeding")
        return None

    def load(self, file):
        """ """
        raise NotImplementedError

    def load_from_dir(self, root_dir, data_dir) -> list:
        """
        Load data from a directory
        """
        compiled_data = []
        if not root_dir:
            LOGGER.warning("Seeding directory not configured properly")
            return compiled_data

        for file in self.load_files(root_dir, data_dir):
            data = self.load(file)
            data = self.validate_data(data, file)
            if data:
                compiled_data.append(data)

        return compiled_data

    def load_files(
        self, root_dir: str, data_dir: str
    ) -> typing.Union[typing.Generator, typing.Iterable]:
        """
        Load data from files inside a directory
        """
        raise NotImplementedError
