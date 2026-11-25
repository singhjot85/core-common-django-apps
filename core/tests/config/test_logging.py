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
from django.test import override_settings

from core.config.logging import (
    convert_loglevel,
    create_log_config,
    get_logging_config,
)
from core.config.logging.filters import (
    ConsoleNoiseFilter,
    SensitiveContentFilter,
    SkipAutoreloadFilter,
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
        assert "skip_autoreload" in filters
        assert "console_noise" in filters
        assert (
            filters["require_debug_true"]["()"] == "django.utils.log.RequireDebugTrue"
        )
        assert (
            filters["require_debug_false"]["()"] == "django.utils.log.RequireDebugFalse"
        )
        assert (
            filters["skip_autoreload"]["()"]
            == "core.config.logging.filters.SkipAutoreloadFilter"
        )
        assert (
            filters["console_noise"]["()"]
            == "core.config.logging.filters.ConsoleNoiseFilter"
        )

    def test_skip_autoreload_filter_drops_autoreload_records(self):
        """
        SkipAutoreloadFilter filters out records from django.utils.autoreload.
        """
        log_filter = SkipAutoreloadFilter()
        reload_record = logging.LogRecord(
            name="django.utils.autoreload",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="Watching for file changes",
            args=(),
            exc_info=None,
        )
        app_record = logging.LogRecord(
            name="core.apps.users",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="User created",
            args=(),
            exc_info=None,
        )

        assert log_filter.filter(reload_record) is False
        assert log_filter.filter(app_record) is True

    def test_console_noise_filter_allows_app_logs_and_errors(self):
        """
        ConsoleNoiseFilter permits errors and app logs while blocking noisy packages.
        """
        noise_filter = ConsoleNoiseFilter()

        # Error from any library is allowed
        error_record = logging.LogRecord(
            name="urllib3.connectionpool",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="Connection failed",
            args=(),
            exc_info=None,
        )
        assert noise_filter.filter(error_record) is True

        # App-level info is allowed
        app_record = logging.LogRecord(
            name="core.apps.users",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="User login successful",
            args=(),
            exc_info=None,
        )
        assert noise_filter.filter(app_record) is True

        # Django server HTTP line is allowed
        server_record = logging.LogRecord(
            name="django.server",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="GET /api/v1/users/ 200",
            args=(),
            exc_info=None,
        )
        assert noise_filter.filter(server_record) is True

        # Blocked noisy records
        db_record = logging.LogRecord(
            name="django.db.backends",
            level=logging.DEBUG,
            pathname=__file__,
            lineno=1,
            msg="SELECT * FROM users",
            args=(),
            exc_info=None,
        )
        assert noise_filter.filter(db_record) is False

        third_party_record = logging.LogRecord(
            name="urllib3.connectionpool",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="Resetting dropped connection",
            args=(),
            exc_info=None,
        )
        assert noise_filter.filter(third_party_record) is False

    @override_settings(DISABLE_SENSITIVE_CONTENT_FILTER=False)
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

    @override_settings(DISABLE_SENSITIVE_CONTENT_FILTER=False)
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

    @override_settings(DISABLE_SENSITIVE_CONTENT_FILTER=False)
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

    @override_settings(DISABLE_SENSITIVE_CONTENT_FILTER=True)
    def test_sensitive_content_filter_disabled_for_local_env(self):
        """When DISABLE_SENSITIVE_CONTENT_FILTER is True, records pass through unmasked."""
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

        assert record.msg == "User with password is secret"

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
        assert info_path.name == "info.log"

        perf_path = CoreLoggingHandlers.FILE_PERF.path()
        assert isinstance(perf_path, Path)
        assert perf_path.name == "perf.log"

        error_path = CoreLoggingHandlers.FILE_ERROR.path()
        assert isinstance(error_path, Path)
        assert error_path.name == "errors.log"

        requests_path = CoreLoggingHandlers.FILE_REQUESTS.path()
        assert isinstance(requests_path, Path)
        assert requests_path.name == "requests.log"

    def test_core_logging_handlers_get_for_logger(self):
        """
        Logger handler routing directs performance, framework, and app loggers correctly.
        """
        requests_handlers = CoreLoggingHandlers.get_for_logger("core.requests")
        assert CoreLoggingHandlers.FILE_REQUESTS.value in requests_handlers

        django_handlers = CoreLoggingHandlers.get_for_logger("django.request")
        assert CoreLoggingHandlers.CONSOLE.value in django_handlers
        assert CoreLoggingHandlers.FILE_ERROR.value in django_handlers

        db_handlers = CoreLoggingHandlers.get_for_logger("django.db.backends")
        assert db_handlers == [CoreLoggingHandlers.FILE_PERF.value]

        autoreload_handlers = CoreLoggingHandlers.get_for_logger(
            "django.utils.autoreload"
        )
        assert autoreload_handlers == []

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
