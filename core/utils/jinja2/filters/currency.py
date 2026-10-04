from decimal import Decimal
from typing import Optional, Union


def format_currency(
    value: Optional[Union[Decimal, float, int, str]],
    symbol: str = "$",
) -> str:
    """Format a numeric value as a currency string."""
    if value is None or value == "":
        return f"{symbol}0.00"
    try:
        dec_val = Decimal(str(value))
        return f"{symbol}{dec_val:,.2f}"
    except Exception:
        return f"{symbol}{value}"
