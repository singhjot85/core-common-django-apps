"""
Logging filters for security and runtime environment routing.

Provides filters for masking sensitive PII/secrets and gating
log records based on the Django DEBUG state.
"""

import logging
from enum import Enum

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
    """

    SENSITIVE = "sensitive", "core.config.logging.filters.SensitiveContentFilter"
    DEBUG_TRUE = "require_debug_true", "django.utils.log.RequireDebugTrue"
    DEBUG_FALSE = "require_debug_false", "django.utils.log.RequireDebugFalse"


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
