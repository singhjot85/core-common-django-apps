from django.conf import settings
from django.core.cache import cache
from django.core.serializers.json import DjangoJSONEncoder
from django.db import connection, models
from django.template import Context, Template
from django.utils.translation import gettext_lazy as _

from core.utils.models.base_models.version_base import BaseSemanticVersionModel


class DefaultTemplateTypeChoices(models.TextChoices):
    """Default template type choices."""

    BASE_TEMPLATE = "base_template", _("Base Template")


class BaseTemplateModel(BaseSemanticVersionModel):
    """
    Base Model for versioned templates (e.g. email, invoice, SMS templates).

    Inherits UUID primary key, timestamps, and semantic versioning from
    BaseSemanticVersionModel. Provides template content fields and rendering helpers.

    Attributes:
        interface_type (CharField): Identifier or category choice for the template.
        plain_content (TextField): Plain text template body.
        html_content (TextField): HTML template body.
        template_mapping (JSONField): Default variables / placeholders mapping for rendering.
    """

    INTERFACE_TYPE = DefaultTemplateTypeChoices.choices
    TEMPLATE_FIELD_PRIORITY = ("html_content", "plain_content")

    is_active = models.BooleanField(default=True, null=False, blank=False)
    interface_type = models.CharField(
        max_length=255, null=False, blank=False, choices=INTERFACE_TYPE
    )
    plain_content = models.TextField(
        verbose_name=_("Text Template content"), null=True, blank=True
    )
    html_content = models.TextField(
        verbose_name=_("HTML Template content"), null=True, blank=True
    )
    template_mapping = models.JSONField(
        verbose_name=_("JSON Mapping for template variables."),
        default=dict,
        null=True,
        blank=True,
        encoder=DjangoJSONEncoder,
    )

    class Meta:
        abstract = True

    @property
    def cache_key(self):
        return self.get_cache_key(self.interface_type)

    @classmethod
    def get_cache_key(cls, interface_type):
        return f"{connection.schema_name}:{cls._meta.app_label}:{cls._meta.model_name}:{interface_type}"

    def save(self, *args, **kwargs):
        cache.delete(self.cache_key)
        return super().save(*args, **kwargs)

    @classmethod
    def get_template_source(
        cls, interface_type: str, field: str | None = None
    ) -> str | None:
        """
        Get a single source field for multipart templates.
        """
        serialized_template = cls.get_template(interface_type)
        if field:
            return serialized_template.get(field)
        for f in cls.TEMPLATE_FIELD_PRIORITY:
            if not serialized_template.get(f, False):
                continue
            return serialized_template.get(f)

        return None

    @classmethod
    def get_template(cls, interface_type: str) -> dict:
        cache_key = cls.get_cache_key(interface_type)
        if serialized_template := cache.get(cache_key, None):
            return serialized_template

        template_obj = (
            cls.objects.latest_qs(
                ("interface_type",), interface_type=interface_type, is_active=True
            )
            .distinct("interface_type")
            .first()
        )

        serialized_template = (
            cls.serialize_for_cache(template_obj) if template_obj else {}
        )
        cache.set(
            cache_key,
            serialized_template,
            timeout=settings.CACHE_SMALL_TIMEOUT,
        )

        return serialized_template

    @classmethod
    def serialize_for_cache(cls, obj: "BaseTemplateModel | None") -> dict:
        if not obj:
            return {}
        return {"plain_content": obj.plain_content, "html_content": obj.html_content}

    def render_using_django_engine(
        self, context: dict
    ) -> tuple[str | None, str | None]:
        """
        Render plain and HTML content using Django's template engine.

        Args:
            context: Context dictionary passed to the template.

        Returns:
            tuple: (html_rendered_content, plain_text_rendered_content)
        """
        html_render, text_render = (None, None)

        if self.html_content:
            html_render = Template(self.html_content).render(Context(context))
        if self.plain_content:
            text_render = Template(self.plain_content).render(
                Context(context, autoescape=False)
            )

        return html_render, text_render

    def render_template(
        self, rendering_context: dict | None = None, engine: str | None = None
    ) -> tuple[str | None, str | None]:
        """
        Render template content with variables from template_mapping and rendering_context.

        Merges defaults from template_mapping with overriding dynamic variables
        from rendering_context.

        Args:
            rendering_context: Dynamic runtime variables to merge into context.
            engine: Template engine to use ('django' or None).

        Returns:
            tuple: (html_rendered_content, plain_text_rendered_content)

        Raises:
            NotImplementedError: If an unsupported template engine is specified.
        """
        complete_context = dict(self.template_mapping or {})
        if rendering_context:
            complete_context.update(rendering_context)

        if not engine or engine.lower() == "django":
            return self.render_using_django_engine(complete_context)

        raise NotImplementedError(f"Template engine '{engine}' is not supported.")
