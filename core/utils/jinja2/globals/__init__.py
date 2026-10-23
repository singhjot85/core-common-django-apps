"""
Jinja2 global function registrations.
"""

from core.utils.jinja2.filters import CORE_FILTERS
from core.utils.labels import get_default_labels, resolve_labels

from .urls import CORE_URL_GLOBALS

CORE_GLOBALS = {
    **CORE_URL_GLOBALS,
    **CORE_FILTERS,
    "resolve_labels": resolve_labels,
    "labels": get_default_labels(),
}

__all__ = ["CORE_GLOBALS", "CORE_URL_GLOBALS"]
