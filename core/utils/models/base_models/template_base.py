from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
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
