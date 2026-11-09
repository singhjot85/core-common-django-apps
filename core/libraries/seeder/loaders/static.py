import json
import logging
import pathlib
import typing

from django.conf import settings

from core.libraries.seeder.exceptions import SeederDataLoaderException
from core.libraries.seeder.loaders.base import BaseFileDataSource

LOGGER = logging.getLogger(__name__)
if typing.TYPE_CHECKING:
    from factory.django import DjangoModelFactory


class FileBasedLoader(BaseFileDataSource):
    """ """

    loader_type: str = "file_loader"

    def load_files(self, root_dir: str, data_dir: str):
        """ """
        path = pathlib.Path(root_dir) / data_dir
        if not path.exists():
            LOGGER.error(f"Path {path} is configured for seeder but not available")
            return

        if not path.is_dir():
            raise SeederDataLoaderException(
                self.loader_type, f"Given data path is not a directory: {path}"
            )

        return sorted(path.glob("*.json"))

    def load(self, file: pathlib.Path):
        """ """
        return json.loads(file.read_text(encoding="utf-8"))

    def get_data(self) -> list:
        """ """
        compiled_data = []

        setup_path = getattr(settings, "SETUP_DIR", None)
        compiled_data.extend(self.load_from_dir(setup_path, self.dir_name))

        core_setup_path = getattr(settings, "CORE_SETUP_DIR", None)
        compiled_data.extend(self.load_from_dir(core_setup_path, self.dir_name))

        return compiled_data


class FactoryBasedLoader(FileBasedLoader):
    """ """

    def __init__(self, factory, directory_name, load_method=None):
        """ """
        self.factory: "DjangoModelFactory" = factory
        super().__init__(directory_name, load_method)

    def validate_data(self, data, file):
        """ """
        data = super().validate_data(data, file)
        if data:
            if isinstance(data, dict):
                data = [data]

            randomized_data = []
            for item in data:
                randomized_data.append(self.factory.stub(**item).__dict__)

        return randomized_data
