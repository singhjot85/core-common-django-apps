"""
Jinja2 integration utilities for the core framework.

Provides:
- Jinja2Backend: Django template backend scanning `<app>/templates/` directories.
- jinja2_environment: Environment factory for application UI templates.
- jinja2_sandboxed_environment: Immutable sandboxed environment for dynamic/DB templates.
- SafeDatabaseLoader: Multi-tenant database template loader with filesystem fallback.
- render, render_block: Helper routines for safe sandboxed template rendering.
"""

from .backend import Jinja2Backend
from .environment import (
    jinja2_environment,
    jinja2_sandboxed_enviournment,
    jinja2_sandboxed_environment,
    render,
    render_block,
)
from .loaders import SafeDatabaseLoader

__all__ = [
    "Jinja2Backend",
    "SafeDatabaseLoader",
    "jinja2_environment",
    "jinja2_sandboxed_environment",
    "jinja2_sandboxed_enviournment",
    "render",
    "render_block",
]
