"""
Logger hierarchy and routing configuration.

Defines default logger configurations for Django framework namespaces,
Celery execution, performance telemetry, and application loggers.
"""

import typing

from core.config.logging import (
    LOG_LEVEL_DEBUG,
    LOG_LEVEL_ERROR,
    LOG_LEVEL_INFO,
    LOG_LEVEL_WARN,
)
from core.config.logging.handlers import CoreLoggingHandlers

CONFIGURED_LOGGERS = [
    "django",
    "django.server",
    "django.request",
    "django.db.backends",
    "django.core.cache",
    "django.utils.autoreload",
    "django.security",
    "celery",
    "celery.task",
    "performance",
    "perf",
]


def create_loggers() -> dict[str, dict[str, typing.Any]]:
    """
    Build dictionary configuration for standard framework and application loggers.

    Returns:
        dict[str, dict[str, typing.Any]]: Dictionary of loggers compatible with dictConfig.
    """
    return {
        "django": {
            "handlers": [
                CoreLoggingHandlers.FILE_INFO.value,
                CoreLoggingHandlers.FILE_ERROR.value,
            ],
            "level": LOG_LEVEL_INFO,
            "propagate": False,
        },
        "django.server": {
            "handlers": [
                CoreLoggingHandlers.CONSOLE.value,
                CoreLoggingHandlers.FILE_INFO.value,
            ],
            "level": LOG_LEVEL_INFO,
            "propagate": False,
        },
        "django.request": {
            "handlers": [
                CoreLoggingHandlers.CONSOLE.value,
                CoreLoggingHandlers.FILE_ERROR.value,
                CoreLoggingHandlers.FILE_INFO.value,
            ],
            "level": LOG_LEVEL_ERROR,
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": [CoreLoggingHandlers.FILE_PERF.value],
            "level": LOG_LEVEL_DEBUG,
            "propagate": False,
        },
        "django.core.cache": {
            "handlers": [CoreLoggingHandlers.FILE_PERF.value],
            "level": LOG_LEVEL_DEBUG,
            "propagate": False,
        },
        "django.utils.autoreload": {
            "handlers": [],
            "level": LOG_LEVEL_WARN,
            "propagate": False,
        },
        "django.security": {
            "handlers": [
                CoreLoggingHandlers.CONSOLE.value,
                CoreLoggingHandlers.FILE_ERROR.value,
                CoreLoggingHandlers.FILE_INFO.value,
            ],
            "level": LOG_LEVEL_WARN,
            "propagate": False,
        },
        "celery": {
            "handlers": [
                CoreLoggingHandlers.CONSOLE.value,
                CoreLoggingHandlers.FILE_INFO.value,
                CoreLoggingHandlers.FILE_ERROR.value,
            ],
            "level": LOG_LEVEL_INFO,
            "propagate": False,
        },
        "celery.task": {
            "handlers": [
                CoreLoggingHandlers.CONSOLE.value,
                CoreLoggingHandlers.FILE_PERF.value,
                CoreLoggingHandlers.FILE_ERROR.value,
            ],
            "level": LOG_LEVEL_INFO,
            "propagate": False,
        },
        "performance": {
            "handlers": [
                CoreLoggingHandlers.FILE_PERF.value,
                CoreLoggingHandlers.FILE_ERROR.value,
            ],
            "level": LOG_LEVEL_DEBUG,
            "propagate": False,
        },
        "perf": {
            "handlers": [
                CoreLoggingHandlers.FILE_PERF.value,
                CoreLoggingHandlers.FILE_ERROR.value,
            ],
            "level": LOG_LEVEL_DEBUG,
            "propagate": False,
        },
    }
