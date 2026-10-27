from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.models import StatusModel, TimeStampedModel, UUIDModel


class DefaultLogStatusChoices(models.TextChoices):
    """
    Default Choices for a logging model
    """

    CREATED = "created", _("Created")
    IN_PROGRESS = "in_progress", _("In Progress")
    QUEUED = "queued", _("Queued")
    SUCESS = "succeded", _("Succeded")
    FAILED = "failed", _("Failed")


class DefaultLogTypeChoices(models.TextChoices):
    """
    Default Choices for a logging model
    """

    INFO = "info", _("Info")
    WARNING = "warning", _("Warning")
    ERROR = "error", _("Error")
    CRITICAL = "critical", _("Critical")


class BaseLogModel(UUIDModel, TimeStampedModel, StatusModel):
    """
    Base Model for any log(s) related models

    Attributes:
        id (uuid): Sets the primary key for the model to a uuid field.
        created (DateTimeField): Adds the created field that gets auto-updated on model creation.
        modified (DateTimeField): Adds the modified field that gets auto-updated on model update(s).
        status (CharField): Sets a Choice(s) Based Charfield that takes choices from ``STATUS`` class attribute.
        status_changed (DateTimeField): Tacks the status change date-time.
    """

    DEFAULT_ORDERING = ("-created", "-modified", "-pk")

    STATUS = DefaultLogStatusChoices.choices

    # TODO: Remove message_type and all dependency; Status already gives granular view on failure's
    # This field is only needed, when failure's are tpo categorized like: critical, noise, etc..
    # Although helpful but not worth keeing on a base model.
    message_type = models.CharField(
        max_length=124,
        null=True,
        blank=True,
        default=DefaultLogTypeChoices.INFO,
        verbose_name=_("Message Type"),
    )
    message = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Message"),
    )
    traceback = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Traceback"),
    )

    class Meta:
        abstract = True
