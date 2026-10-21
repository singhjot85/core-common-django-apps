from .currency import format_currency
from .dates import format_date, format_datetime

CORE_FILTERS = {
    "format_date": format_date,
    "format_datetime": format_datetime,
    "format_currency": format_currency,
    "currency": format_currency,
}

CORE_SAFE_FILTERS = {
    "format_date": format_date,
    "format_datetime": format_datetime,
    "format_currency": format_currency,
    "currency": format_currency,
}

__all__ = [
    "CORE_SAFE_FILTERS",
    "CORE_FILTERS",
    "format_currency",
    "format_date",
    "format_datetime",
]
