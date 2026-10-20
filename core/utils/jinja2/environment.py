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
def jinja2_sandboxed_environment() -> ImmutableSandboxedEnvironment:
    """
    Factory function for the sandboxed Jinja2 environment used for
    dynamic, database-backed, or user-editable templates.
    """
    dirs = [str(d) for d in getattr(settings, "SANDBOX_TEMPLATES_DIRS", []) if d]
    fallback_loader = FileSystemLoader(dirs) if dirs else None

    env = ImmutableSandboxedEnvironment(
        loader=SafeDatabaseLoader(fallback_loader),
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


# Backward compatibility alias for typo
jinja2_sandboxed_enviournment = jinja2_sandboxed_environment


def render(template_name: str, context: dict | None = None) -> str:
    """
    Render a sandboxed template (database or file-backed).
    Pass plain dicts/dataclasses, NEVER ORM objects.
    """
    return (
        jinja2_sandboxed_environment().get_template(template_name).render(context or {})
    )


def render_block(template_name: str, block: str, context: dict | None = None) -> str:
    """
    Render one named block, e.g. {% block subject %} of an email template.
    """
    template = jinja2_sandboxed_environment().get_template(template_name)
    ctx = template.new_context(context or {})
    return "".join(template.blocks[block](ctx)).strip()
