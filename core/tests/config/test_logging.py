"""
Unit tests for core framework logging configuration.

Validates log level conversion, filters, formatters, handlers,
and dictionary configuration generation for Python dictConfig.
"""

import logging
import logging.config
from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured

from core.config.logging import (
    convert_loglevel,
    create_log_config,
    get_logging_config,
)
from core.config.logging.filters import (
    SensitiveContentFilter,
    create_filters,
)
from core.config.logging.formatters import (
    ColoredConsoleFormatter,
    ConsoleColors,
    LogFormats,
    LoggingFormatters,
    create_formatters,
)
from core.config.logging.handlers import (
    CoreLoggingHandlers,
    create_console_handler,
    create_handlers,
)
from core.utils.checks import is_development, is_production
from core.utils.error_handling.content_masking import ContentMaskingUtils


class TestConvertLogLevel:
    """
    Test suite for convert_loglevel helper.
    """

    @pytest.mark.parametrize(
        ("level_name", "expected_level"),
        [
            ("DEBUG", logging.DEBUG),
            ("INFO", logging.INFO),
            ("WARNING", logging.WARNING),
            ("ERROR", logging.ERROR),
            ("CRITICAL", logging.CRITICAL),
            ("PERFORMANCE", 35),
            ("info", logging.INFO),
            (" debug ", logging.DEBUG),
        ],
    )
    def test_convert_loglevel_valid_strings(self, level_name, expected_level):
        """
        Valid log level string names return corresponding integer level.
        """
        assert convert_loglevel(level_name) == expected_level

    def test_convert_loglevel_integer_passthrough(self):
        """
        Integer log level passes through unchanged.
        """
        assert convert_loglevel(logging.INFO) == logging.INFO

    def test_convert_loglevel_invalid_name_raises_error(self):
        """
        Unrecognized log level string raises ImproperlyConfigured.
        """
        with pytest.raises(ImproperlyConfigured, match="Invalid log level"):
            convert_loglevel("INVALID_LEVEL")

    def test_convert_loglevel_invalid_type_raises_error(self):
        """
        Non-string and non-int argument raises ImproperlyConfigured.
        """
        with pytest.raises(ImproperlyConfigured, match="Invalid log level type"):
            convert_loglevel([1, 2, 3])


class TestLoggingFilters:
    """
    Test suite for logging filters.
    """

    def test_create_filters_contains_expected_keys(self):
        """
        create_filters returns dictConfig mapping for sensitive and debug filters.
        """
        filters = create_filters()

        assert "sensitive" in filters
        assert "require_debug_true" in filters
        assert "require_debug_false" in filters
        assert (
            filters["require_debug_true"]["()"] == "django.utils.log.RequireDebugTrue"
        )
        assert (
            filters["require_debug_false"]["()"] == "django.utils.log.RequireDebugFalse"
        )

    def test_sensitive_content_filter_masks_string_message(self):
        """
        SensitiveContentFilter replaces sensitive patterns in record.msg.
        """
        log_filter = SensitiveContentFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="User with password is secret",
            args=(),
            exc_info=None,
        )

        log_filter.filter(record)

        assert "secret" not in record.msg
        assert "*******" in record.msg

    def test_sensitive_content_filter_masks_dict_message(self):
        """
        SensitiveContentFilter sanitizes dictionary keys and values in record.msg.
        """
        log_filter = SensitiveContentFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg={
                "password": "supersecretpassword",  # pragma: allowlist secret
                "username": "alice",
            },
            args=(),
            exc_info=None,
        )

        log_filter.filter(record)

        assert record.msg["password"] == "********"  # pragma: allowlist secret
        assert record.msg["username"] == "alice"

    def test_sensitive_content_filter_masks_tuple_args(self):
        """
        SensitiveContentFilter sanitizes string and dict items within record.args tuple.
        """
        log_filter = SensitiveContentFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="Login attempt for %s with payload %s",
            args=("password", {"secret_key": "mysecret"}),  # pragma: allowlist secret
            exc_info=None,
        )

        log_filter.filter(record)

        assert isinstance(record.args, tuple)
        assert record.args[0] == ContentMaskingUtils.mask_value
        assert record.args[1]["secret_key"] == "********"

    def test_sensitive_content_filter_handles_none_args(self):
        """
        SensitiveContentFilter executes cleanly when record.args is None or empty.
        """
        log_filter = SensitiveContentFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="Plain informational message",
            args=None,
            exc_info=None,
        )

        assert log_filter.filter(record) is True
        assert record.msg == "Plain informational message"


class TestLoggingFormatters:
    """
    Test suite for logging formatters and colorizer.
    """

    def test_create_formatters_structure(self):
        """
        create_formatters returns dictionary with format strings for each enum member.
        """
        formatters = create_formatters()

        for member in LoggingFormatters:
            assert member.value in formatters
            formatter_config = formatters[member.value]
            assert isinstance(formatter_config, dict)
            assert "format" in formatter_config

    def test_colored_console_formatter_applies_ansi_codes(self):
        """
        ColoredConsoleFormatter wraps formatted output in ANSI color codes.
        """
        formatter = ColoredConsoleFormatter(fmt=LogFormats.SIMPLE)
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="An error occurred",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)

        assert ConsoleColors.RED in formatted
        assert ConsoleColors.RESET in formatted
        assert "An error occurred" in formatted


class TestLoggingHandlers:
    """
    Test suite for logging handler definitions and factories.
    """

    def test_core_logging_handlers_path(self):
        """
        File-based handlers return resolved Path objects while stream handlers return None.
        """
        assert CoreLoggingHandlers.CONSOLE.path() is None
        assert CoreLoggingHandlers.MAIL_ADMIN.path() is None

        info_path = CoreLoggingHandlers.FILE_INFO.path()
        assert isinstance(info_path, Path)
        assert "info.log" in str(info_path)

    def test_core_logging_handlers_get_for_logger(self):
        """
        Django loggers receive dependency file handler while app loggers receive standard set.
        """
        django_handlers = CoreLoggingHandlers.get_for_logger("django.request")
        assert django_handlers == [CoreLoggingHandlers.FILE_DEPS.value]

        app_handlers = CoreLoggingHandlers.get_for_logger("core.apps.users")
        assert CoreLoggingHandlers.CONSOLE.value in app_handlers
        assert CoreLoggingHandlers.FILE_INFO.value in app_handlers
        assert CoreLoggingHandlers.FILE_ERROR.value in app_handlers

    def test_create_handlers_contains_all_core_handlers(self):
        """
        create_handlers returns valid dictConfig configurations for all defined handlers.
        """
        handlers = create_handlers()

        for member in CoreLoggingHandlers:
            assert member.value in handlers
            handler_config = handlers[member.value]
            assert "class" in handler_config

    def test_create_console_handler_configuration(self):
        """
        Console handler configures StreamHandler with colored formatter and sensitive filter.
        """
        config = create_console_handler()

        assert config["class"] == "logging.StreamHandler"
        assert config["formatter"] == LoggingFormatters.COLORED.value
        assert "sensitive" in config["filters"]


class TestLoggingConfigFactory:
    """
    Test suite for create_log_config and get_logging_config.
    """

    def test_create_log_config_dict_config_compatibility(self):
        """
        create_log_config produces a complete schema loadable by logging.config.dictConfig.
        """
        config = create_log_config()

        assert config["version"] == 1
        assert config["disable_existing_loggers"] is False
        assert "filters" in config
        assert "formatters" in config
        assert "handlers" in config
        assert "loggers" in config
        assert "root" in config

        # Verify that Python logging dictConfig parses it without errors
        logging.config.dictConfig(config)

    def test_get_logging_config_with_none_path(self):
        """
        get_logging_config returns default configuration when path is None.
        """
        config = get_logging_config(None)
        assert "version" in config
        assert "handlers" in config

    def test_get_logging_config_with_invalid_path_falls_back(self):
        """
        get_logging_config falls back to default configuration when path cannot be resolved.
        """
        config = get_logging_config("non_existent_module_path")
        assert "version" in config
        assert "handlers" in config


class TestRuntimeEnvironmentChecks:
    """
    Test suite for is_production and is_development runtime check helpers.
    """

    def test_is_production_and_is_development_consistency(self):
        """
        is_development returns exact logical negation of is_production.
        """
        assert is_development() == (not is_production())
