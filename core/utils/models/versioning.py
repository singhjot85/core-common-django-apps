from django.db import models


class InvalidVersionException(Exception):
    """Raised when a version is invalid"""

    pass


class SimpleVersionModelMixin(models.Model):
    DEFAULT_ORDERING = ("-version_major", "-version_minor", "-version_patch")
    DEFAULT_VERSION = (1, 0, 0)

    version_major = models.IntegerField(
        null=True, blank=True, default=DEFAULT_VERSION[0]
    )
    version_minor = models.IntegerField(
        null=True, blank=True, default=DEFAULT_VERSION[1]
    )
    version_patch = models.IntegerField(
        null=True, blank=True, default=DEFAULT_VERSION[2]
    )
    version = models.CharField(
        null=True,
        blank=True,
        default=f"{DEFAULT_VERSION[0]}.{DEFAULT_VERSION[1]}.{DEFAULT_VERSION[2]}",
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.resolve_version()
        return super().save(*args, **kwargs)

    def validate_version(self):
        if not self.version:
            return self.DEFAULT_VERSION

        try:
            major, minor, patch = map(int, self.version.split("."))
            return major, minor, patch
        except Exception as e:
            raise InvalidVersionException from e

    def resolve_version(self):
        if self.version:
            (
                self.version_major,
                self.version_minor,
                self.version_patch,
            ) = self.validate_version()
        else:
            self.version = (
                f"{self.version_major}.{self.version_minor}.{self.version_patch}"
            )
