import logging
import typing

from django.apps import apps as django_apps
from django.core.cache import cache
from jinja2 import BaseLoader, TemplateNotFound

LOGGER = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    from core.utils.models.base_models import BaseTemplateModel


class SafeDatabaseLoader(BaseLoader):
    def __init__(self, fallback_loader: BaseLoader | None = None):
        self.fallback_loader = fallback_loader

    def get_template_model(
        self, app_name: str, model_name: str
    ) -> type["BaseTemplateModel"]:
        """
        Get template model from given app_name and model_name.
        """
        return typing.cast(
            type["BaseTemplateModel"],
            django_apps.get_model(f"{app_name}.{model_name}", require_ready=True),
        )

    def generate_filename(
        self, app_name: str, model_name: str, interface_type: str
    ) -> str:
        """Generate a virtual URI filename for the database template."""
        return f"db://{app_name}/{model_name}/{interface_type}"

    def get_source(
        self, environment, template: str
    ) -> tuple[str, str, typing.Callable]:
        """
        Loads template source from database if template identifier matches
        'app_name:model_name:interface_type' or 'db://app_name/model_name/interface_type',
        otherwise delegates to fallback_loader.
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
