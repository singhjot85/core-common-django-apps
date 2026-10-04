from jinja2 import Environment

from core.utils.jinja2.filters import CORE_FILTERS
from core.utils.jinja2.globals import CORE_GLOBALS


def jinja2_environment(**options) -> Environment:
    """
    Factory function for initializing the Jinja2 template Environment.
    Configured in Django settings TEMPLATES backend.
    """
    env = Environment(**options)

    # Register global functions & filters from modular subpackages
    env.globals.update(CORE_GLOBALS)
    env.filters.update(CORE_FILTERS)

    return env
