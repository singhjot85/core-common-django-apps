from django.db import models
from model_utils.models import TimeStampedModel, UUIDModel

from .versioning import SimpleVersionModelMixin


# TODO: Design a better versioning model and then deperecate this file
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
