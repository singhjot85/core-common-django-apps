"""
Logging formatters and ANSI color definitions for console and file output.

Defines format templates for standard, verbose, JSON, simple, error,
and color-coded terminal log outputs.
"""

import logging
import typing
from enum import Enum


class ConsoleColors:
    """
    ANSI color escape codes for terminal formatting.
    """

    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"


class LogFormats:
    """
    Centralized log record format string templates.
    """

    STANDARD = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    VERBOSE = (
        "%(asctime)s - %(levelname)s - %(name)s - %(filename)s:%(lineno)d - %(message)s"
    )
    JSON = "%(asctime)s - %(levelname)s - %(name)s - %(message)s - %(pathname)s"
    SIMPLE = "%(asctime)s - %(levelname)s - %(message)s"
    ERROR = "%(asctime)s - %(levelname)s - %(name)s - %(filename)s:%(lineno)d - %(message)s - %(exc_info)s"


class ColoredConsoleFormatter(logging.Formatter):
    """
    Console log formatter applying level-specific ANSI colors.

    Wraps the standard formatted message with ANSI escape sequences
    corresponding to the record's log level.
    """

    COLORS = {
        "DEBUG": ConsoleColors.BLUE,
        "INFO": ConsoleColors.GREEN,
        "WARNING": ConsoleColors.YELLOW,
        "ERROR": ConsoleColors.RED,
        "CRITICAL": ConsoleColors.MAGENTA,
        "PERFORMANCE": ConsoleColors.CYAN,
    }

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record with level-appropriate ANSI coloring.

        Args:
            record (logging.LogRecord): Log record to format.

        Returns:
            str: Colorized log line ending with ANSI reset sequence.
        """
        log_message = super().format(record)
        color = self.COLORS.get(record.levelname, ConsoleColors.WHITE)
        return f"{color}{log_message}{ConsoleColors.RESET}"


class LoggingFormatters(Enum):
    """
    Enumeration of supported log format configurations.
    """

    ERROR = "error"
    SIMPLE = "simple"
    JSON = "json"
    VERBOSE = "verbose"
    STANDARD = "standard"
    COLORED = "colored"

    def get_format(self) -> dict[str, typing.Any]:
        """
        Return the dictConfig dictionary configuration for this formatter.

        Returns:
            dict[str, typing.Any]: Dictionary configuration expected by logging.config.dictConfig.
        """
        if self == self.__class__.COLORED:
            return {
                "()": "core.config.logging.formatters.ColoredConsoleFormatter",
                "format": LogFormats.STANDARD,
            }

        format_string = getattr(
            LogFormats,
            self.value.upper(),
            LogFormats.STANDARD,
        )
        return {"format": format_string}


def create_formatters() -> dict[str, dict[str, typing.Any]]:
    """
    Build dictionary configuration for all registered log formatters.

    Returns:
        dict[str, dict[str, typing.Any]]: Dictionary of formatters compatible with dictConfig.
    """
    formatters = {}
    for formatter in LoggingFormatters:
        formatters[formatter.value] = formatter.get_format()

    return formatters
