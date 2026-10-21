"""
Jinja2 currency formatting filter.
"""

from decimal import Decimal
from typing import Optional, Union


def format_currency(
    value: Optional[Union[Decimal, float, int, str]],
    symbol: str = "$",
) -> str:
    """
    Format a numeric value as a currency string with comma grouping and 2 decimal places.

    Args:
        value: Numeric value (Decimal, float, int, or string representation).
        symbol: Currency symbol prefix (default: "$").

    Returns:
        Formatted currency string, e.g. "$1,250.50". If value is None or empty, returns "$0.00".
    """
    if value is None or value == "":
        return f"{symbol}0.00"
    try:
        dec_val = Decimal(str(value))
        return f"{symbol}{dec_val:,.2f}"
    except Exception:
        return f"{symbol}{value}"
