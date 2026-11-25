"""
Logging filters for security and runtime environment routing.

Provides filters for masking sensitive PII/secrets, suppressing autoreload spam,
filtering console noise, and gating log records based on the Django DEBUG state.
"""

import logging
import os
from enum import Enum

from django.conf import settings

from core.utils.error_handling.content_masking import (
    ContentMaskingUtils,
    get_sensitive_matcher,
)


class LoggingFilters(Enum):
    """
    Available logging filters mapped to their filter name and dotted class path.

    Attributes:
        SENSITIVE: Mask passwords, tokens, and PII from log records.
        DEBUG_TRUE: Only process records when DEBUG is True.
        DEBUG_FALSE: Only process records when DEBUG is False.
        SKIP_AUTORELOAD: Suppress noisy django.utils.autoreload log records.
        CONSOLE_NOISE: Suppress third-party clutter from terminal output.
    """

    SENSITIVE = "sensitive", "core.config.logging.filters.SensitiveContentFilter"
    DEBUG_TRUE = "require_debug_true", "django.utils.log.RequireDebugTrue"
    DEBUG_FALSE = "require_debug_false", "django.utils.log.RequireDebugFalse"
    SKIP_AUTORELOAD = (
        "skip_autoreload",
        "core.config.logging.filters.SkipAutoreloadFilter",
    )
    CONSOLE_NOISE = (
        "console_noise",
        "core.config.logging.filters.ConsoleNoiseFilter",
    )


class SkipAutoreloadFilter(logging.Filter):
    """
    Filter that suppresses noisy autoreload logs.

    Prevents frequent file-watching poll messages emitted by Django's
    reloader from cluttering files and console output.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Determine whether the log record should be kept.

        Args:
            record (logging.LogRecord): The log record to inspect.

        Returns:
            bool: False if record originates from django.utils.autoreload, True otherwise.
        """
        return not record.name.startswith("django.utils.autoreload")


class ConsoleNoiseFilter(logging.Filter):
    """
    Filter that restricts terminal output to app logs, allowed packages, and errors.

    Allows all ERROR and CRITICAL records regardless of source, while suppressing
    noisy third-party libraries and internal Django plumbing at DEBUG/INFO.
    """

    ALLOWED_NAMESPACES = (
        "core",
        "sample_project",
        "apps",
        "django.server",
        "celery",
    )

    BLOCKED_PATTERNS = (
        "django.utils.autoreload",
        "django.db.backends",
        "django.core.cache",
    )

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Determine whether the log record should appear on the shell console.

        Args:
            record (logging.LogRecord): The log record to evaluate.

        Returns:
            bool: True if allowed on console, False otherwise.
        """
        if record.levelno >= logging.ERROR:
            return True

        for blocked in self.BLOCKED_PATTERNS:
            if record.name == blocked or record.name.startswith(f"{blocked}."):
                return False

        project_name = os.getenv("PROJECT_NAME")
        allowed_prefixes = list(self.ALLOWED_NAMESPACES)
        if project_name and project_name not in allowed_prefixes:
            allowed_prefixes.append(project_name)

        for allowed in allowed_prefixes:
            if record.name == allowed or record.name.startswith(f"{allowed}."):
                return True

        return False


class SensitiveContentFilter(logging.Filter):
    """
    Filter that masks sensitive content in log messages and record arguments.

    Sanitizes string messages and argument values (including dictionaries
    and lists) using ContentMaskingUtils to prevent secrets and PII from
    leaking into log destinations.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Sanitize record.msg and record.args in-place.

        Side effects:
        - Mutates ``record.msg`` and ``record.args`` to replace sensitive values with masks.

        Args:
            record (logging.LogRecord): The log record to inspect and sanitize.

        Returns:
            bool: Always True to allow record processing to continue.
        """
        if settings.configured and getattr(
            settings, "DISABLE_SENSITIVE_CONTENT_FILTER", False
        ):
            return True

        if record.msg:
            if isinstance(record.msg, str):
                matcher = get_sensitive_matcher()
                record.msg = ContentMaskingUtils.filter_value(record.msg, matcher)
            elif isinstance(record.msg, dict):
                record.msg = ContentMaskingUtils.filter_sensitive_content(
                    stringified=False, deep_search=True, **record.msg
                )

        if record.args:
            if isinstance(record.args, dict):
                record.args = ContentMaskingUtils.filter_sensitive_content(
                    stringified=False, deep_search=True, **record.args
                )
            elif isinstance(record.args, (tuple, list)):
                matcher = get_sensitive_matcher()
                masked_args = []
                for item in record.args:
                    if isinstance(item, str):
                        masked_args.append(
                            ContentMaskingUtils.filter_value(item, matcher)
                        )
                    elif isinstance(item, dict):
                        masked_args.append(
                            ContentMaskingUtils.filter_sensitive_content(
                                stringified=False, deep_search=True, **item
                            )
                        )
                    else:
                        masked_args.append(item)
                record.args = (
                    tuple(masked_args)
                    if isinstance(record.args, tuple)
                    else masked_args
                )

        return super().filter(record)


def create_filters() -> dict[str, dict[str, str]]:
    """
    Build dictionary configuration for all registered logging filters.

    Returns:
        dict[str, dict[str, str]]: Dictionary of filters compatible with dictConfig.
    """
    filters = {}
    for member in LoggingFilters:
        filter_name, filter_class = member.value
        filters[filter_name] = {"()": filter_class}

    return filters
