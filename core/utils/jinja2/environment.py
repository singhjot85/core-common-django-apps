import datetime
from decimal import Decimal
from typing import Optional, Union

from django.middleware.csrf import get_token
from django.templatetags.static import static
from django.urls import reverse
from jinja2 import Environment, pass_context
from markupsafe import Markup


@pass_context
def csrf_input(context: dict) -> Markup:
    """Render the hidden CSRF token input tag."""
    request = context.get("request")
    if request:
        token = get_token(request)
    else:
        token = context.get("csrf_token", "")
    return Markup(f'<input type="hidden" name="csrfmiddlewaretoken" value="{token}">')


@pass_context
def csrf_token_val(context: dict) -> str:
    """Get the current CSRF token string for JavaScript requests."""
    request = context.get("request")
    if request:
        return get_token(request)
    return str(context.get("csrf_token", ""))


def format_date(
    value: Optional[Union[datetime.date, datetime.datetime, str]],
    fmt: str = "%b %d, %Y",
) -> str:
    """Format a date or datetime object into a human-readable string."""
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
    value: Optional[Union[datetime.datetime, str]], fmt: str = "%b %d, %Y, %I:%M %p"
) -> str:
    """Format a datetime object into a human-readable date & time string."""
    return format_date(value, fmt=fmt)


def format_currency(
    value: Optional[Union[Decimal, float, int, str]], symbol: str = "$"
) -> str:
    """Format a number or Decimal as currency."""
    if value is None or value == "":
        return f"{symbol}0.00"
    try:
        dec_val = Decimal(str(value))
        return f"{symbol}{dec_val:,.2f}"
    except Exception:
        return f"{symbol}{value}"


def jinja2_environment(**options) -> Environment:
    """
    Factory function for initializing the Jinja2 template Environment.
    Configured in Django settings TEMPLATES backend.
    """
    env = Environment(**options)

    # Global template functions
    env.globals.update(
        {
            "static": static,
            "url": reverse,
            "format_date": format_date,
            "format_datetime": format_datetime,
            "format_currency": format_currency,
        }
    )

    # Custom filters
    env.filters.update(
        {
            "format_date": format_date,
            "format_datetime": format_datetime,
            "currency": format_currency,
        }
    )

    return env
