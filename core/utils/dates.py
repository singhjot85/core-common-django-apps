from datetime import date, datetime
from typing import Optional, Union

from django.utils import timezone


def get_local_datetime(
    dt: Optional[datetime] = None,
    *,
    naive_is_utc: bool = True,
) -> datetime:
    """
    Return a timezone-aware datetime in Django's configured TIME_ZONE.

    Args:
        dt:
            - None  -> returns the current time in local timezone.
            - naive datetime -> assumed to be UTC (if naive_is_utc=True)
                               or local time (if naive_is_utc=False),
                               then converted to local timezone.
            - aware datetime -> converted to local timezone.
        naive_is_utc:
            How to interpret naive datetimes. Ignored if dt is aware or None.

    Returns:
        An aware datetime object in settings.TIME_ZONE.
    """
    tz = timezone.get_current_timezone()

    if dt is None:
        return timezone.localtime(timezone.now(), tz)

    if timezone.is_naive(dt):
        if naive_is_utc:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = timezone.make_aware(dt, tz)

    return timezone.localtime(dt, tz)


def get_local_date(
    dt: Optional[Union[datetime, date]] = None,
    *,
    naive_is_utc: bool = True,
) -> date:
    """
    Return a date object in Django's configured TIME_ZONE.

    Args:
        dt:
            - None  -> today's date in local timezone.
            - date  -> returned as-is (dates have no time component).
            - naive datetime -> interpreted per naive_is_utc, then localized.
            - aware datetime -> converted to local timezone, then date extracted.
        naive_is_utc:
            How to interpret naive datetimes.

    Returns:
        A date object representing the local calendar date.
    """
    if isinstance(dt, datetime):
        return get_local_datetime(dt, naive_is_utc=naive_is_utc).date()

    if isinstance(dt, date):
        return dt

    if dt is None:
        return timezone.localdate(timezone.now())

    raise TypeError(f"Unsupported type: {type(dt)!r}")
