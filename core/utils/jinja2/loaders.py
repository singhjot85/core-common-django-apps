"""
Database-backed Jinja2 template loader with filesystem fallback.

Enables loading dynamically stored, multi-tenant templates from models
subclassing `BaseTemplateModel`.
"""

import logging
import typing

from django.apps import apps as django_apps
from django.core.cache import cache
from jinja2 import BaseLoader, TemplateNotFound

LOGGER = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    from core.utils.models.base_models import BaseTemplateModel


class SafeDatabaseLoader(BaseLoader):
    """
    Jinja2 template loader that resolves templates from database models with filesystem fallback.

    Template identifiers can be expressed in two formats:
    1. Colon-delimited: `app_name:model_name:interface_type`
       (e.g., `"invoices:invoicetemplate:standard"`)
    2. Virtual URI: `db://app_name/model_name/interface_type`
       (e.g., `"db://invoices/invoicetemplate/standard"`)

    If the template identifier does not match a database pattern, or if no database
    record is active for that interface type, lookup delegates to the optional
    `fallback_loader` (e.g. `FileSystemLoader`).

    Cache Invalidation:
    - For database templates: checked against the model's Redis cache key.
    - For file templates: verified against the file's mtime and invalidated if a database
      override is subsequently created.

    Attributes:
        fallback_loader (BaseLoader | None): Optional fallback loader for file-backed templates.
    """

    def __init__(self, fallback_loader: BaseLoader | None = None):
        """
        Initialize the SafeDatabaseLoader.

        Args:
            fallback_loader: Optional Jinja2 BaseLoader instance (e.g. FileSystemLoader)
                to delegate to when a template is not stored in the database.
        """
        self.fallback_loader = fallback_loader

    def get_template_model(
        self, app_name: str, model_name: str
    ) -> type["BaseTemplateModel"]:
        """
        Dynamically resolve a concrete or abstract template model class.

        Args:
            app_name: Django application label (e.g., 'invoices').
            model_name: Model class name (e.g., 'InvoiceTemplate' or 'invoicetemplate').

        Returns:
            The Django Model class subclassing BaseTemplateModel.

        Raises:
            LookupError: If the app or model cannot be resolved from Django apps registry.
        """
        return typing.cast(
            type["BaseTemplateModel"],
            django_apps.get_model(f"{app_name}.{model_name}", require_ready=True),
        )

    def generate_filename(
        self, app_name: str, model_name: str, interface_type: str
    ) -> str:
        """
        Generate a virtual URI filename for the database template.

        Args:
            app_name: Django app label.
            model_name: Django model name.
            interface_type: Category/interface identifier of the template.

        Returns:
            Virtual URI string formatted as `db://<app_name>/<model_name>/<interface_type>`.
        """
        return f"db://{app_name}/{model_name}/{interface_type}"

    def get_source(
        self, environment, template: str
    ) -> tuple[str, str, typing.Callable]:
        """
        Load template source from the database or delegate to the fallback loader.

        Args:
            environment: The active Jinja2 Environment instance.
            template: Template name or database identifier string.

        Returns:
            tuple: (source_code, filename_or_virtual_uri, uptodate_callable)

        Raises:
            TemplateNotFound: If the template cannot be found in the database or fallback loader.
        """
        normalized_template = template
        if normalized_template.startswith("db://"):
            normalized_template = normalized_template[5:].replace("/", ":")

        if ":" in normalized_template:
            parts = normalized_template.split(":")
            if len(parts) == 3:
                app_name, model_name, interface_type = parts
                try:
                    TemplateModel = self.get_template_model(app_name, model_name)
                except Exception as exc:
                    LOGGER.warning(
                        "Unable to resolve template model %s.%s for template %s: %s",
                        app_name,
                        model_name,
                        template,
                        exc,
                    )
                    if self.fallback_loader:
                        return self.fallback_loader.get_source(environment, template)
                    raise TemplateNotFound(template) from exc

                def peek_cache_for_template() -> bool:
                    cache_key = TemplateModel.get_cache_key(interface_type)
                    return cache.get(cache_key, None) is not None

                source = TemplateModel.get_template_source(interface_type)
                if source is not None:
                    filename = self.generate_filename(
                        app_name, model_name, interface_type
                    )
                    return source, filename, peek_cache_for_template

                if self.fallback_loader:
                    source, filename, fs_uptodate = self.fallback_loader.get_source(
                        environment, template
                    )

                    def uptodate() -> bool:
                        if peek_cache_for_template():
                            return False
                        return fs_uptodate() if fs_uptodate else True

                    return source, filename, uptodate

                raise TemplateNotFound(template)

        # Standard file-backed template: delegate to fallback loader without warning
        if self.fallback_loader:
            return self.fallback_loader.get_source(environment, template)

        raise TemplateNotFound(template)
