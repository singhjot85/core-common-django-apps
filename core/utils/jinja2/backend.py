"""
Custom Jinja2 template backend for Django.
"""

from django.template.backends.jinja2 import Jinja2


class Jinja2Backend(Jinja2):
    """
    Custom Jinja2 template backend for Django.

    By default, Django's built-in `Jinja2` backend looks for templates inside
    `<app>/jinja2/` directories when `APP_DIRS=True`. `Jinja2Backend` overrides
    `app_dirname` to `"templates"` so that Jinja2 templates reside alongside
    standard Django app layouts (e.g. `core/templates/` or `<app>/templates/`),
    differentiated by file extensions (e.g. `.jinja`).

    Attributes:
        app_dirname (str): Directory name inside installed apps to search for templates ("templates").
    """

    app_dirname = "templates"
