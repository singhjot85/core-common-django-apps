import logging
import typing

from django.apps import apps as django_apps
from django.core.cache import cache
from jinja2 import BaseLoader

LOGGER = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    from core.utils.models.base_models import BaseTemplateModel


class SafeDatabaseLoader(BaseLoader):
    def __init__(self, fallback_loader: BaseLoader):
        self.fallback_loader = fallback_loader

    def get_template_model(self, app_name, model_name) -> type["BaseTemplateModel"]:
        """
        Get template model from given app_name and model_name
        """
        return typing.cast(
            type["BaseTemplateModel"],
            django_apps.get_model(f"{app_name}.{model_name}", require_ready=True),
        )

    def generate_filename(self, app_name, model_name, interface_type):
        """ """
        return f"db://{app_name}/{model_name}/{interface_type}"

    def get_source(self, environment, template) -> tuple[str, str, typing.Callable]:
        """
        template: app_name:model_name:interface_type
        """
        try:
            app_name, model_name, interface_type = template.partition(":")
            TemplateModel = self.get_template_model(app_name, model_name)
        except Exception:
            LOGGER.warning(
                f"Malformed Template name for crrent loader, Template Name >>> {template}"
            )
            return self.fallback_loader.get_source(environment, template)

        def peek_cache_for_template():
            cache_key = TemplateModel.get_cache_key(interface_type)
            cached_template = cache.get(cache_key, None)
            return False if cached_template is None else True

        source = TemplateModel.get_template_source(interface_type)
        if source is not None:
            filename = self.generate_filename()
            return source, filename, peek_cache_for_template

        # No override. The file-backed template must ALSO go stale when an override appears,
        # otherwise Jinja keeps serving the cached file version until restart.
        source, filename, fs_uptodate = self.fallback_loader.get_source(
            environment, template
        )

        def uptodate():
            if not peek_cache_for_template():
                return False
            return fs_uptodate() if fs_uptodate else True

        return source, filename, uptodate
