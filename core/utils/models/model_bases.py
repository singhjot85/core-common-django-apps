from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.models import StatusModel, TimeStampedModel, UUIDModel

from .soft_delete import DeletionTrackingModel
from .versioning import SimpleVersionModelMixin


class AbstractParty(models.Model):
    """Abstract Helper to give common party related attributes to a model

    Provide Attributes:
        suffix (CharField): Suffix for Name
        first_name (CharField): First name attribute.
        middle_name (CharField): Middle name attribute.
        last_name (CharField): Last name attribute.
        business_name (CharField): Business name attribute.
    """

    suffix = models.CharField(null=True, blank=True, default=None)
    first_name = models.CharField(null=True, blank=True, default=None)
    middle_name = models.CharField(null=True, blank=True, default=None)
    last_name = models.CharField(null=True, blank=True, default=None)
    business_name = models.CharField(null=True, blank=True, default=None)

    class Meta:
        abstract = True

    @property
    def full_name(self) -> str:
        """Return the combined full name or business_name."""
        name_parts = [self.first_name, self.middle_name, self.last_name]
        name = " ".join(part for part in name_parts if part).strip()
        if name:
            if self.suffix:
                return f"{name} {self.suffix}".strip()
            return name
        return self.business_name or ""


class AbstractAddress(models.Model):
    """Abstract Helper to give common address attributes to a model.

    Provides Attributes:
        address_line_1 (CharField): Primary street address or building details.
        address_line_2 (CharField): Secondary street address / suite / apt.
        landmark (CharField): Nearby landmark.
        city (CharField): City or locality.
        state (CharField): State, province, or region.
        postal_code (CharField): Postal / PIN / Zip code.
        country (CharField): Country name or ISO country code (default 'IN').
    """

    address_line_1 = models.CharField(max_length=255, null=True, blank=True)
    address_line_2 = models.CharField(max_length=255, null=True, blank=True)
    landmark = models.CharField(max_length=128, null=True, blank=True)
    city = models.CharField(max_length=128, null=True, blank=True)
    state = models.CharField(max_length=128, null=True, blank=True)
    postal_code = models.CharField(max_length=32, null=True, blank=True)
    country = models.CharField(max_length=64, default="IN", null=True, blank=True)

    class Meta:
        abstract = True

    @property
    def full_address(self) -> str:
        parts = [
            self.address_line_1,
            self.address_line_2,
            self.landmark,
            self.city,
            self.state,
            self.postal_code,
            self.country,
        ]
        return ", ".join(p for p in parts if p)


class BaseModel(UUIDModel, TimeStampedModel, DeletionTrackingModel):
    """Base Model to be used by most of the models,

    Attributes:
        id (uuid): Sets the primary key for the model to a uuid field.
        created (DateTimeField): Adds the created field that gets auto-updated on model creation.
        modified (DateTimeField): Adds the modified field that gets auto-updated on model update(s).
        is_removed (BooleanField): Is the Model Soft Deleted
        removed_by (ForeignKey): User that deleted the instance
    """

    DEFAULT_ORDERING = ("-created", "-modified", "-pk")

    class Meta:
        abstract = True

    @classmethod
    def get_object(cls, **unique_filters) -> models.Model:
        """
        Getter to fetch database object for current class
        It uses ``available_objects.get``, as we have ``SotDeleteModel``, this is necessary

        Kwargs:
            unique_filters that define's a unique object

        Raises:
            ObjectNotFound
        """
        from core.utils.models.helpers import safe_get_object_or_raise

        return safe_get_object_or_raise(cls, **unique_filters)


class DefaultLogStatusChoices(models.TextChoices):
    """
    Default Choices for a logging model
    """

    CREATED = "created", _("Created")
    IN_PROGRESS = "in_progress", _("In Progress")
    QUEUED = "queued", _("Queued")
    SUCESS = "succeded", _("Succeded")
    FAILED = "failed", _("Failed")


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

    class Meta:
        abstract = True


class BaseVersioningModel(UUIDModel, TimeStampedModel, SimpleVersionModelMixin):
    """Base Model to be used by models with Versioning,

    Attributes:
        id (uuid): Sets the primary key for the model to a uuid field.
        created (DateTimeField): Adds the created field that gets auto-updated on model creation.
        modified (DateTimeField): Adds the modified field that gets auto-updated on model update(s).
        version_major, *_minor, *_patch (IntegerField): Three integer fields
        version (CharField): Semantic Version value.
    """

    _major = "major"
    _minor = "minor"
    _patch = "patch"

    _bump_types = (_major, _minor, _patch)

    @classmethod
    def _get_latest_object(cls, **filters) -> models.Model:
        """Get latest object from Database."""
        return cls.objects.filter(**filters).order_by(cls.DEFAULT_ORDERING).first()

    @classmethod
    def get_latest_versions(cls, **filters) -> tuple[int, int, int]:
        """Get latest versions from Database."""
        obj = cls._get_latest_object(**filters)
        return (
            obj.version_major,
            obj.version_minor,
            (
                obj.version_patch
                if obj
                else f"{cls.DEFAULT_VERSION[0]}.{cls.DEFAULT_VERSION[1]}.{cls.DEFAULT_VERSION[2]}"
            ),
        )

    @classmethod
    def get_latest_version(cls, **filters) -> str:
        """Get latest version from Database."""
        obj = cls._get_latest_object(**filters)
        return (
            obj.version
            if obj
            else f"{cls.DEFAULT_VERSION[0]}.{cls.DEFAULT_VERSION[1]}.{cls.DEFAULT_VERSION[2]}"
        )

    def bump_version(self, bump_type: str):
        """
        TODO: Don't like this method, this could be better
        """
        major, minor, patch = self.version_major, self.version_minor, self.version_patch

        if bump_type == self._major:
            major += 1
        elif bump_type == self._minor:
            minor += 1
        elif bump_type == self._patch:
            patch += 1

        self.version_major = major
        self.version_minor = minor
        self.version_patch = patch
        self.save()

    class Meta:
        abstract = True
