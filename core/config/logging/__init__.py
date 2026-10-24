"""
Core framework logging package.

Provides declarative configuration factories, constants, formatters,
filters, and handlers for Django and Celery application logging.
"""

import importlib
import logging
import os
import typing
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

LOG_LEVEL_DEBUG = "DEBUG"
LOG_LEVEL_INFO = "INFO"
LOG_LEVEL_WARN = "WARNING"
LOG_LEVEL_ERROR = "ERROR"
LOG_LEVEL_CRITICAL = "CRITICAL"
LOG_LEVEL_PERF = "PERFORMANCE"

LOG_LEVELS: dict[str, int] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "PERFORMANCE": 35,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def convert_loglevel(level: typing.Union[str, int]) -> int:
    """
    Convert a string or integer log level representation to its integer level.

    Args:
        level (str | int): Name or numeric value of the logging level.

    Returns:
        int: Standard integer logging level.

    Raises:
        ImproperlyConfigured:
        - Provided level is neither string nor int.
        - String level is not a recognized logging level name.
    """
    if isinstance(level, int):
        return level

    if not isinstance(level, str):
        raise ImproperlyConfigured(f"Invalid log level type: {type(level).__name__}")

    normalized = level.strip().upper()
    if normalized in LOG_LEVELS:
        return LOG_LEVELS[normalized]

    mapping = logging.getLevelNamesMapping()
    if normalized not in mapping:
        raise ImproperlyConfigured(f"Invalid log level: {level}")

    return mapping[normalized]


# ------------------------
#   Logging Variables
# ------------------------
LOG_DIR_PATH = os.getenv("BACKEND_LOG_DIRECTORY", "backend/logs")
APP_LOG_LEVEL = convert_loglevel(os.getenv("BACKEND_LOG_LEVEL", LOG_LEVEL_ERROR))

APP_LOGFILE_BYTES = int(os.getenv("BACKEND_LOGFILE_BYTES", 50 * 1024 * 1024))  # 50MB
APP_LOGFILE_BACKUP_COUNT = int(os.getenv("BACKEND_LOGFILE_BACKUPS", 2))
LOG_DIR = Path(LOG_DIR_PATH)


def create_log_config() -> dict[str, typing.Any]:
    """
    Build the complete logging configuration dictionary for Django settings.

    Side effects:
    - Imports filter, formatter, handler, and logger definition modules.

    Returns:
        dict[str, typing.Any]: Dictionary configuration ready for logging.config.dictConfig.
    """
    from core.config.logging.filters import create_filters  # noqa: PLC0415
    from core.config.logging.formatters import create_formatters  # noqa: PLC0415
    from core.config.logging.handlers import (  # noqa: PLC0415
        CoreLoggingHandlers,
        create_handlers,
    )
    from core.config.logging.loggers import create_loggers  # noqa: PLC0415

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": create_filters(),
        "formatters": create_formatters(),
        "handlers": create_handlers(),
        "loggers": create_loggers(),
        "root": {
            "handlers": CoreLoggingHandlers.get_for_logger("root"),
            "level": APP_LOG_LEVEL,
        },
    }


def get_logging_config(path: typing.Optional[str] = None) -> dict[str, typing.Any]:
    """
    Resolve and return logging configuration, preferring a custom path if provided.

    Attempts to load a ``LOGGING`` dictionary from the dotted module path.
    Falls back to ``create_log_config()`` if the path is not provided, cannot be
    imported, or does not declare ``LOGGING``.

    Args:
        path (str, optional): Dotted Python module path to a custom logging module.
            Defaults to None.

    Returns:
        dict[str, typing.Any]: Logging configuration dictionary.
    """
    if not path:
        return create_log_config()

    try:
        module = importlib.import_module(path)
        custom_config = getattr(module, "LOGGING", None)
        if isinstance(custom_config, dict):
            return custom_config
    except (ImportError, AttributeError):
        pass

    return create_log_config()


__all__ = [
    "LOG_LEVEL_DEBUG",
    "LOG_LEVEL_INFO",
    "LOG_LEVEL_WARN",
    "LOG_LEVEL_ERROR",
    "LOG_LEVEL_CRITICAL",
    "LOG_LEVEL_PERF",
    "LOG_LEVELS",
    "APP_LOG_LEVEL",
    "APP_LOGFILE_BYTES",
    "APP_LOGFILE_BACKUP_COUNT",
    "LOG_DIR",
    "convert_loglevel",
    "create_log_config",
    "get_logging_config",
]
