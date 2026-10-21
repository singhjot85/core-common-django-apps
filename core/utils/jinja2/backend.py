"""
Custom Jinja2 template backend for Django.
"""

from typing import Any

from django.template import TemplateDoesNotExist
from django.template.backends.jinja2 import Jinja2


class Jinja2Backend(Jinja2):
    """
    Custom Jinja2 template backend for Django.

    By default, Django's built-in `Jinja2` backend looks for templates inside
    `<app>/jinja2/` directories when `APP_DIRS=True`. `Jinja2Backend` overrides
    `app_dirname` to `"templates"` so that Jinja2 templates reside alongside
    standard Django app layouts (e.g. `core/templates/` or `<app>/templates/`),
    differentiated by file extensions (e.g. `.jinja`, `.jinja2`).

    To prevent collision with Django's default DTL engine (which renders Django
    Admin, DRF browsable API, etc.), `Jinja2Backend` only resolves templates matching
    `allowed_extensions`. Any other template request raises `TemplateDoesNotExist`,
    allowing Django to fall back to the DTL engine.

    Attributes:
        app_dirname (str): Directory name inside installed apps to search for templates ("templates").
        default_allowed_extensions (tuple[str, ...]): Recognized Jinja2 template file extensions.
    """

    app_dirname = "templates"
    default_allowed_extensions: tuple[str, ...] = (".jinja", ".jinja2")

    def __init__(self, params: dict[str, Any]):
        params = params.copy()
        options = params.get("OPTIONS", {})
        self.allowed_extensions = tuple(
            options.pop("allowed_extensions", self.default_allowed_extensions)
        )
        super().__init__(params)

    def get_template(self, template_name: str):
        """
        Retrieve a compiled Jinja2 template if its extension matches `allowed_extensions`.

        Args:
            template_name: The path or name of the template.

        Returns:
            django.template.backends.jinja2.Template

        Raises:
            TemplateDoesNotExist: If the template does not have an allowed extension
                or cannot be found by Jinja2's loader.
            TemplateSyntaxError: If the Jinja2 template contains invalid syntax.
        """
        if not template_name.endswith(self.allowed_extensions):
            raise TemplateDoesNotExist(template_name, backend=self)

        return super().get_template(template_name)
