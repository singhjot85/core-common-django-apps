"""
Jinja2 Environment factories and rendering routines.

Provides:
- jinja2_environment: Configured for Django's TEMPLATES setting for standard UI pages.
- jinja2_sandboxed_environment: Restricted environment for user-editable / DB templates.
- render, render_block: Convenience routines for rendering sandboxed templates.
"""

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

    Configured in Django settings `TEMPLATES[0]["OPTIONS"]["environment"]`.
    Registers core global functions (`url`, `static`) and format filters
    (`format_date`, `format_currency`).

    Args:
        **options: Keyword options passed from Django's TEMPLATES configuration,
            such as `loader`, `autoescape`, `auto_reload`, and `undefined`.

    Returns:
        A fully configured Jinja2 Environment instance for application UI rendering.
    """
    from core.utils.labels import resolve_labels  # noqa: PLC0415

    env = Environment(**options)

    # Register global functions & filters from modular subpackages
    env.globals.update(CORE_GLOBALS)
    env.filters.update(CORE_FILTERS)
    env.globals.update({"resolve_labels": resolve_labels})

    return env


@lru_cache(maxsize=1)
def jinja2_sandboxed_environment() -> ImmutableSandboxedEnvironment:
    """
    Factory function for the sandboxed Jinja2 environment.

    Used for rendering dynamic, database-backed, or tenant-customized templates
    (e.g., invoice HTML, email bodies, SMS notifications) safely.

    Security & Isolation features:
    - Inherits from `ImmutableSandboxedEnvironment` to prevent template authors from
      mutating variables, accessing private attributes (`_`), or executing dangerous code.
    - Uses `StrictUndefined` to immediately raise errors on undefined template variables.
    - Uses `SafeDatabaseLoader` with fallback to `SANDBOX_TEMPLATES_DIRS`.
    - Only registers `CORE_SAFE_FILTERS`.

    Returns:
        Cached singleton instance of ImmutableSandboxedEnvironment.
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


# Backward compatibility alias for earlier typo
jinja2_sandboxed_enviournment = jinja2_sandboxed_environment


def render(template_name: str, context: dict | None = None) -> str:
    """
    Render a sandboxed template (database-backed or file-backed).

    Args:
        template_name: Template identifier (e.g. 'invoices:invoicetemplate:standard'
            or 'email/welcome.html').
        context: Context dictionary. Pass plain dicts or dataclasses, NEVER live ORM models.

    Returns:
        Rendered string output.
    """
    return (
        jinja2_sandboxed_environment().get_template(template_name).render(context or {})
    )


def render_block(template_name: str, block: str, context: dict | None = None) -> str:
    """
    Render a single named block of a template (e.g. {% block subject %} of an email).

    Args:
        template_name: Template identifier string.
        block: Name of the Jinja2 block to render.
        context: Context dictionary of variables.

    Returns:
        Rendered string content of the specified block with surrounding whitespace stripped.
    """
    template = jinja2_sandboxed_environment().get_template(template_name)
    ctx = template.new_context(context or {})
    return "".join(template.blocks[block](ctx)).strip()
