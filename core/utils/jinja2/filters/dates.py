import datetime
from typing import Optional, Union


def format_date(
    value: Optional[Union[datetime.date, datetime.datetime, str]],
    fmt: str = "%b %d, %Y",
) -> str:
    """Format a date or datetime object into a human-readable date string."""
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
    """Format a datetime object into a human-readable date & time string."""
    return format_date(value, fmt=fmt)
