"""
Logger hierarchy and routing configuration.

Defines default logger configurations for Django framework namespaces
and application loggers.
"""

import typing

from core.config.logging import APP_LOG_LEVEL
from core.config.logging.handlers import CoreLoggingHandlers

CONFIGURED_LOGGERS = [
    # "django",
    "django.request",
    "django.db.backends",
    "django.security",
]


def create_loggers() -> dict[str, dict[str, typing.Any]]:
    """
    Build dictionary configuration for standard framework and application loggers.

    Returns:
        dict[str, dict[str, typing.Any]]: Dictionary of loggers compatible with dictConfig.
    """
    loggers = {}
    for logger_name in CONFIGURED_LOGGERS:
        config = {
            "propagate": False,
            "level": APP_LOG_LEVEL,
            "handlers": CoreLoggingHandlers.get_for_logger(logger_name),
        }
        loggers[logger_name] = config

    return loggers
