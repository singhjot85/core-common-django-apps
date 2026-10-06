from core.utils.jinja2.filters import CORE_FILTERS

from .urls import CORE_URL_GLOBALS

CORE_GLOBALS = {
    **CORE_URL_GLOBALS,
    **CORE_FILTERS,
}

__all__ = ["CORE_GLOBALS", "CORE_URL_GLOBALS"]
