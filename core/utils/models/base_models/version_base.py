from model_utils.models import TimeStampedModel, UUIDModel

from core.utils.models.version import SemanticVersioningModel


class BaseSemanticVersionModel(UUIDModel, TimeStampedModel, SemanticVersioningModel):
    """
    Base Model to be used by models with Semantic Versioning.

    Combines UUID primary key, created/modified timestamps, and semantic
    versioning fields and methods.

    Attributes:
        id (UUIDField): Primary key for the model.
        created (DateTimeField): Auto-updated on model creation.
        modified (DateTimeField): Auto-updated on model update(s).
        version_major (IntegerField): Major version integer.
        version_minor (IntegerField): Minor version integer.
        version_patch (IntegerField): Patch version integer.
        version (CharField): Semantic Version string ('X.Y.Z').
    """

    _major = "major"
    _minor = "minor"
    _patch = "patch"

    _bump_types = (_major, _minor, _patch)

    class Meta:
        abstract = True
