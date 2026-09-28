import importlib
import inspect
from pathlib import Path


def load_file_from_package(
    target_filename, file_path: str = None, target_class: type = None
):
    """
    Load a target file from current file's package

    Example usage:
    >>> load_file_from_package("interfaces", __file__)
    ... load_file_from_package("interfaces", self)
    ... load_file_from_package("interfaces", cls)

    """
    if not file_path and not target_class:
        raise ImportError("Unable to import file")

    if file_path:
        module = Path(file_path).__module__
    else:
        module = target_class.__module__

    package = module.rsplit(".", 1)[0]
    target_file = None
    try:
        target_file = importlib.import_module(f"{package}.{target_filename}")
    except ModuleNotFoundError:
        pass

    return target_file


def classes_from_file(file=None, file_path: str = None):
    """
    Get all the classe from a given file.
    Usage:
    >>> file = load_file_from_package("interfaces", __file__)
    ... classes_from_file(file)
    """

    if not file:
        file_path, filename = file_path.rsplit(".", 1)
        file = load_file_from_package(file_path, filename)

    classes = []
    for _, klass in inspect.getmembers(file, inspect.isclass):
        classes.append(klass)

    return classes
