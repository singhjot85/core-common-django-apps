"""
Core logging handlers configuration.

Configures console, rotating file, and admin email handlers
tailored for development and production environments.
"""

import sys
import typing
from enum import Enum
from pathlib import Path

from core.config.logging import (
    APP_LOG_LEVEL,
    APP_LOGFILE_BACKUP_COUNT,
    APP_LOGFILE_BYTES,
    LOG_DIR,
    LOG_LEVEL_DEBUG,
    LOG_LEVEL_ERROR,
    LOG_LEVEL_INFO,
    LOG_LEVELS,
)
from core.config.logging.filters import LoggingFilters
from core.config.logging.formatters import LoggingFormatters
from core.utils.checks import is_development, is_production


class CoreLoggingHandlers(Enum):
    """
    Standard logging handlers defined across the core framework.

    Attributes:
        CONSOLE: Colorized stdout stream handler.
        FILE_INFO: Rotating file handler for informational logs.
        FILE_ERROR: Rotating file handler for error and critical logs.
        FILE_JSON: Rotating file handler formatted for JSON ingestion.
        FILE_DEPS: Rotating file handler dedicated to third-party/django dependencies.
        FILE_PERF: Rotating file handler dedicated to performance telemetry.
        FILE_REQUESTS: Rotating file handler dedicated to incoming HTTP request logs.
        MAIL_ADMIN: Email handler dispatching errors to administrators in production.
    """

    CONSOLE = "console"
    FILE_INFO = "file_info"
    FILE_ERROR = "file_error"
    FILE_JSON = "file_json"
    FILE_DEPS = "file_dependencies"
    FILE_PERF = "file_performance"
    FILE_REQUESTS = "file_requests"
    MAIL_ADMIN = "mail_admins"

    def path(self) -> typing.Optional[Path]:
        """
        Return the filesystem path for file-based handlers.

        Returns:
            Path | None: Target log file path, or None for stream/email handlers.
        """
        if self in (self.__class__.CONSOLE, self.__class__.MAIL_ADMIN):
            return None

        file_name_map = {
            self.__class__.FILE_INFO: "info.log",
            self.__class__.FILE_PERF: "perf.log",
            self.__class__.FILE_REQUESTS: "requests.log",
            self.__class__.FILE_ERROR: "errors.log",
            self.__class__.FILE_JSON: "json.log",
            self.__class__.FILE_DEPS: "dependencies.log",
        }
        filename = file_name_map.get(self, f"{self.value}.log")
        return LOG_DIR / filename

    def log_level(self) -> int:
        """
        Return the integer logging level designated for this handler.

        Returns:
            int: Standard logging level integer.
        """
        logger_level_map = {
            self.__class__.FILE_INFO.value: LOG_LEVELS[LOG_LEVEL_INFO],
            self.__class__.FILE_REQUESTS.value: LOG_LEVELS[LOG_LEVEL_INFO],
            self.__class__.FILE_ERROR.value: LOG_LEVELS[LOG_LEVEL_ERROR],
            self.__class__.FILE_PERF.value: LOG_LEVELS[LOG_LEVEL_DEBUG],
        }
        return logger_level_map.get(self.value, APP_LOG_LEVEL)

    @classmethod
    def get_for_logger(cls, logger_name: str) -> list[str]:
        """
        Resolve handler names assigned to a given logger namespace.

        Args:
            logger_name (str): Name of the logger to resolve handlers for.

        Returns:
            list[str]: List of handler name strings to attach.
        """
        if logger_name in ("django.db.backends", "django.core.cache"):
            return [cls.FILE_PERF.value]

        if logger_name in ("performance", "perf"):
            return [cls.FILE_PERF.value, cls.FILE_ERROR.value]

        if logger_name in ("core.requests", "requests"):
            return [cls.FILE_REQUESTS.value, cls.FILE_ERROR.value]

        if logger_name == "django.utils.autoreload":
            return []

        if logger_name == "django.server":
            return [cls.CONSOLE.value, cls.FILE_INFO.value]

        if logger_name in ("django.request", "django.security"):
            return [cls.CONSOLE.value, cls.FILE_ERROR.value, cls.FILE_INFO.value]

        if logger_name == "celery.task":
            return [cls.CONSOLE.value, cls.FILE_PERF.value, cls.FILE_ERROR.value]

        if logger_name.startswith("django"):
            return [cls.FILE_INFO.value, cls.FILE_ERROR.value]

        return [
            cls.CONSOLE.value,
            cls.FILE_INFO.value,
            cls.FILE_ERROR.value,
        ]


def create_console_handler() -> dict[str, typing.Any]:
    """
    Build StreamHandler configuration targeting stdout.

    Returns:
        dict[str, typing.Any]: dictConfig handler dictionary.
    """
    filter_names = [
        LoggingFilters.SENSITIVE.value[0],
        LoggingFilters.CONSOLE_NOISE.value[0],
    ]
    if is_production():
        filter_names.append(LoggingFilters.DEBUG_FALSE.value[0])

    return {
        "class": "logging.StreamHandler",
        "stream": sys.stdout,
        "formatter": LoggingFormatters.COLORED.value,
        "filters": filter_names,
        "level": APP_LOG_LEVEL,
    }


def create_file_handler(
    handler: typing.Union[CoreLoggingHandlers, str],
) -> dict[str, typing.Any]:
    """
    Build RotatingFileHandler configuration for development environments.

    In non-development environments, falls back to a console stream handler.

    Side effects:
    - Creates destination directory structure for the target log file.

    Args:
        handler (CoreLoggingHandlers | str): Handler enum or string identifier.

    Returns:
        dict[str, typing.Any]: dictConfig handler dictionary.
    """
    if not is_development():
        return create_console_handler()

    handler_enum = (
        handler
        if isinstance(handler, CoreLoggingHandlers)
        else CoreLoggingHandlers(handler)
    )
    log_file_path = handler_enum.path()
    if log_file_path:
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

    formatter = (
        LoggingFormatters.JSON.value
        if handler_enum == CoreLoggingHandlers.FILE_JSON
        else LoggingFormatters.STANDARD.value
    )

    filters = [
        LoggingFilters.SENSITIVE.value[0],
    ]
    if handler_enum == CoreLoggingHandlers.FILE_INFO:
        filters.append(LoggingFilters.SKIP_AUTORELOAD.value[0])

    return {
        "class": "logging.handlers.RotatingFileHandler",
        "filename": str(log_file_path),
        "maxBytes": APP_LOGFILE_BYTES,
        "backupCount": APP_LOGFILE_BACKUP_COUNT,
        "formatter": formatter,
        "filters": filters,
        "level": handler_enum.log_level(),
    }


def create_handlers() -> dict[str, dict[str, typing.Any]]:
    """
    Build dictionary configuration for all core logging handlers.

    Returns:
        dict[str, dict[str, typing.Any]]: Dictionary of handlers compatible with dictConfig.
    """
    handlers = {}
    for handler in CoreLoggingHandlers:
        if handler.value.startswith("file_"):
            handlers[handler.value] = create_file_handler(handler)
        elif handler == CoreLoggingHandlers.MAIL_ADMIN:
            handlers[handler.value] = {
                "class": "django.utils.log.AdminEmailHandler",
                "level": LOG_LEVELS[LOG_LEVEL_ERROR],
                "filters": [LoggingFilters.DEBUG_FALSE.value[0]],
            }
        else:
            handlers[handler.value] = create_console_handler()

    return handlers
