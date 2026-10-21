"""
Jinja2 date and datetime formatting filters.
"""

import datetime
from typing import Optional, Union


def format_date(
    value: Optional[Union[datetime.date, datetime.datetime, str]],
    fmt: str = "%b %d, %Y",
) -> str:
    """
    Format a date, datetime, or ISO-formatted string into a human-readable date.

    Args:
        value: Date, datetime, or ISO string (e.g. '2026-10-05').
        fmt: strftime format string (default: "%b %d, %Y" -> "Oct 05, 2026").

    Returns:
        Formatted date string. Returns "-" if value is None or empty.
    """
    if value is None or value == "":
        return "-"
    if isinstance(value, str):
        try:
            value = datetime.datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return value
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.strftime(fmt)
    return str(value)


def format_datetime(
    value: Optional[Union[datetime.datetime, str]],
    fmt: str = "%b %d, %Y, %I:%M %p",
) -> str:
    """
    Format a datetime object or ISO string into a human-readable date & time string.

    Args:
        value: Datetime object or ISO formatted datetime string.
        fmt: strftime format string (default: "%b %d, %Y, %I:%M %p" -> "Oct 05, 2026, 02:30 PM").

    Returns:
        Formatted datetime string. Returns "-" if value is None or empty.
    """
    return format_date(value, fmt=fmt)
