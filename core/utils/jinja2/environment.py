from functools import lru_cache

from django.conf import settings
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from jinja2.sandbox import ImmutableSandboxedEnvironment

from core.utils.jinja2.filters import CORE_FILTERS, CORE_SAFE_FILTERS
from core.utils.jinja2.globals import CORE_GLOBALS
from core.utils.jinja2.loaders import SafeDatabaseLoader


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


@lru_cache(maxsize=1)
def jinja2_sandboxed_enviournment():
    """ """
    dirs = [str(d) for d in getattr(settings, "SANDBOX_TEMPLATES_DIRS", [])]
    env = ImmutableSandboxedEnvironment(
        loader=SafeDatabaseLoader(FileSystemLoader(dirs)),
        autoescape=select_autoescape(
            enabled_extensions=("html", "xml", "json"),
            default_for_string=True,
            default=False,
        ),
        undefined=StrictUndefined,
        auto_reload=True,
        cache_size=400,
    )
    env.filters.update(CORE_SAFE_FILTERS)
    return env


def render(template_name, context):
    """
    render("email/welcome.html", {...}). Pass plain dicts/dataclasses, NEVER ORM objects.

    """
    return jinja2_sandboxed_enviournment().get_template(template_name).render(**context)


def render_block(template_name, block, context):
    """
    Render one named block, e.g. {% block subject %} of an email template.

    """
    template = jinja2_sandboxed_enviournment().get_template(template_name)
    return "".join(template.blocks[block](template.new_context(context))).strip()
