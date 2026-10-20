import typing

from django.db import models, transaction
from django.db.models.utils import resolve_callables

from core.utils.dirtyfields import DirtyFieldsMixin


class InvalidVersionException(Exception):
    """Raised when a semantic version or version part is invalid."""

    pass


def validate_version(value: str) -> None:
    """
    Validate that a given string conforms to semantic versioning (Major.Minor.Patch).

    Args:
        value: The version string to validate.

    Raises:
        InvalidVersionException: If the value is not a string, does not have 3 parts,
            or if any part cannot be cast to an integer.
    """
    if not isinstance(value, str):
        raise InvalidVersionException("Invalid Version, expected string")

    parts = value.split(".")

    if len(parts) != 3:
        raise InvalidVersionException(
            "Invalid Version, expected format Major.Minor.Patch"
        )

    def int_cast(val, part_type):
        try:
            return int(val)
        except (TypeError, ValueError) as e:
            raise InvalidVersionException(
                f"Invalid Version part, {part_type} should be a valid int"
            ) from e

    int_cast(parts[0], "Version Major")
    int_cast(parts[1], "Version Minor")
    int_cast(parts[2], "Version Patch")


class SemanticVersionQuerySet(models.QuerySet):
    """
    Custom QuerySet methods for SemanticVersioningModel.
    """

    def distinct_qs(self, *field_names, **filters):
        """
        Get a distinct queryset using given filters and distinct field names.

        NOTE: ``.distinct(*fields)`` uses PostgreSQL ``DISTINCT ON``.
        Not portable to MySQL/SQLite.

        Args:
            *field_names: Fields to apply DISTINCT ON.
            **filters: Lookup filters to apply.

        Returns:
            SemanticVersionQuerySet: Filtered and distinct queryset.
        """
        default_ordering = getattr(self.model._meta, "ordering", [])
        return (
            self.filter(**filters)
            .order_by(*field_names, *default_ordering)
            .distinct(*field_names)
        )

    def latest_qs(self, ordering: list | None = None, **filters):
        """
        Return an ordered queryset of versions (latest first).
        Chainable — no DB hit until evaluated.

        Args:
            ordering: Optional additional ordering clauses to append.
            **filters: Lookup filters to apply.

        Returns:
            SemanticVersionQuerySet: Ordered queryset.
        """
        default_ordering = list(
            getattr(
                self.model._meta,
                "ordering",
                ("-version_major", "-version_minor", "-version_patch"),
            )
        )
        if ordering:
            default_ordering = [*default_ordering, *ordering]

        return self.filter(**filters).order_by(*default_ordering)

    def latest_version(
        self, parts: bool = False, **filters
    ) -> typing.Union[tuple[int, int, int], str]:
        """
        Get the latest version of the matched objects.

        NOTE: Returns a value immediately (evaluates queryset).
        For chainable queries, prefer ``latest_qs()``.

        Args:
            parts: If True, returns a tuple of (major, minor, patch) integers.
                   If False, returns the version string 'X.Y.Z'.
            **filters: Lookup filters.

        Returns:
            tuple[int, int, int] | str: The latest version parts or formatted string.
        """
        versions = (
            self.latest_qs(**filters)
            .values_list("version", "version_major", "version_minor", "version_patch")
            .first()
        )
        if not versions:
            if parts:
                return self.model.DEFAULT_VERSION_PARTS
            return self.model.DEFAULT_VERSION

        if parts:
            return versions[1], versions[2], versions[3]

        return versions[0]

    def versioned_get_or_create(
        self, defaults: dict | None = None, **kwargs
    ) -> tuple[models.Model, bool]:
        """
        Get-or-create for a semantic-versioned object.

        Initializes version fields to model defaults if creating.

        Args:
            defaults: Extra fields to set on creation (not used for lookup).
            **kwargs: Lookup attributes.

        Returns:
            tuple (object, created): The instance and boolean created flag.
        """
        create_defaults = dict(defaults or {})
        create_defaults.setdefault("version", self.model.DEFAULT_VERSION)
        create_defaults.setdefault("version_major", self.model.DEFAULT_VERSION_PARTS[0])
        create_defaults.setdefault("version_minor", self.model.DEFAULT_VERSION_PARTS[1])
        create_defaults.setdefault("version_patch", self.model.DEFAULT_VERSION_PARTS[2])
        return self.get_or_create(**kwargs, defaults=create_defaults)

    def versioned_update_or_create(
        self,
        defaults: dict | None = None,
        bump_type: str = "major",
        filters: dict | None = None,
        **kwargs,
    ) -> tuple[models.Model, bool]:
        """
        Update or create for a semantic-versioned object.

        Looks up an object matching the given filters/kwargs. If it exists,
        increments its version according to bump_type and updates it with defaults.
        Otherwise creates a new instance with the default version.

        Args:
            defaults: Dict of attributes to update on the existing object or set on creation.
            bump_type: Version bump type ('major', 'minor', or 'patch').
            filters: Dict of lookup attributes.
            **kwargs: Additional lookup attributes (merged with filters).

        Returns:
            tuple (object, created): The instance and boolean created flag.
        """
        lookup = {**(filters or {}), **kwargs}
        update_defaults = dict(defaults or {})

        def get_bumped_version_parts(major: int, minor: int, patch: int):
            if bump_type == "patch":
                patch += 1
            elif bump_type == "minor":
                minor += 1
                patch = 0
            elif bump_type == "major":
                major += 1
                minor = 0
                patch = 0
            else:
                raise ValueError(
                    f"Invalid bump_type '{bump_type}'. Expected 'major', 'minor', or 'patch'."
                )
            return major, minor, patch

        self._for_write = True
        with transaction.atomic(using=self.db):
            obj, created = self.select_for_update().versioned_get_or_create(
                defaults=update_defaults, **lookup
            )
            if created:
                return obj, created

            major, minor, patch = get_bumped_version_parts(
                obj.version_major, obj.version_minor, obj.version_patch
            )
            new_version = f"{major}.{minor}.{patch}"

            update_defaults.update(
                {
                    "version": new_version,
                    "version_major": major,
                    "version_minor": minor,
                    "version_patch": patch,
                }
            )

            for k, v in resolve_callables(update_defaults):
                setattr(obj, k, v)

            update_fields = set(update_defaults)
            concrete_field_names = self.model._meta._non_pk_concrete_field_names
            # update_fields does not support non-concrete fields.
            if concrete_field_names.issuperset(update_fields):
                # Add fields which are set on pre_save(), e.g. auto_now fields.
                # This is to maintain backward compatibility as these fields
                # are not updated unless explicitly specified in the
                # update_fields list.
                pk_fields = self.model._meta.pk_fields
                for field in self.model._meta.local_concrete_fields:
                    if not (
                        field in pk_fields
                        or field.__class__.pre_save is models.Field.pre_save
                    ):
                        update_fields.add(field.name)
                        if field.name != field.attname:
                            update_fields.add(field.attname)
                obj.save(using=self.db, update_fields=update_fields)
            else:
                obj.save(using=self.db)

        return obj, False


class SemanticVersionManager(models.Manager.from_queryset(SemanticVersionQuerySet)):
    """
    Custom Manager methods for SemanticVersioningModel.
    """

    pass


class SemanticVersioningModel(DirtyFieldsMixin, models.Model):
    """
    Abstract model adding Semantic Versioning (Major.Minor.Patch) support.

    Maintains both human-readable string version ('X.Y.Z') and individual integer
    parts (version_major, version_minor, version_patch) kept automatically in sync.
    """

    DEFAULT_VERSION_PARTS = (1, 0, 0)
    DEFAULT_VERSION = ".".join(map(str, DEFAULT_VERSION_PARTS))

    version_major = models.IntegerField(
        null=True, blank=True, default=DEFAULT_VERSION_PARTS[0]
    )
    version_minor = models.IntegerField(
        null=True, blank=True, default=DEFAULT_VERSION_PARTS[1]
    )
    version_patch = models.IntegerField(
        null=True, blank=True, default=DEFAULT_VERSION_PARTS[2]
    )
    version = models.CharField(
        null=True,
        blank=True,
        validators=[validate_version],
        default=DEFAULT_VERSION,
    )

    objects: SemanticVersionManager = SemanticVersionManager()

    if typing.TYPE_CHECKING:
        objects: SemanticVersionQuerySet

    class Meta:
        ordering = ("-version_major", "-version_minor", "-version_patch")
        abstract = True

    def clean(self):
        """
        Clean fields and validate that all version parts are non-negative and >= 1.0.0.
        """
        super().clean()

        if any(
            p is None
            for p in (self.version_major, self.version_minor, self.version_patch)
        ):
            return

        if self.version_major < 0 or self.version_minor < 0 or self.version_patch < 0:
            raise InvalidVersionException("Version part cannot be negative")

        if (
            self.version_minor == 0
            and self.version_patch == 0
            and self.version_major <= 0
        ):
            raise InvalidVersionException("Version cannot be less than 1.0.0")

    def save(self, *args, **kwargs):  # noqa: DJ012
        """
        Sync version string and integer parts before saving.
        """
        self._sync_version_and_parts()
        return super().save(*args, **kwargs)

    def resolve_version(self):
        """
        Resolve and synchronize version string and integer parts.
        """
        self._sync_version_and_parts()

    def _sync_version_and_parts(self):
        """
        Resolve version and parts from current object state.
        Ensures version string and major/minor/patch integers stay in sync.
        """
        if self._state.adding:
            parts_tuple = (
                self.version_major,
                self.version_minor,
                self.version_patch,
            )
            if self.version and self.version != self.DEFAULT_VERSION:
                self.version_major, self.version_minor, self.version_patch = (
                    self._get_version_parts()
                )
            elif (
                any(p is not None for p in parts_tuple)
                and parts_tuple != self.DEFAULT_VERSION_PARTS
            ):
                self.version = (
                    f"{self.version_major}.{self.version_minor}.{self.version_patch}"
                )
            elif self.version:
                self.version_major, self.version_minor, self.version_patch = (
                    self._get_version_parts()
                )
            elif all(p is not None for p in parts_tuple):
                self.version = (
                    f"{self.version_major}.{self.version_minor}.{self.version_patch}"
                )
            return

        dirty_fields = self.get_dirty_fields()
        if "version" in dirty_fields:
            self.version_major, self.version_minor, self.version_patch = (
                self._get_version_parts()
            )
            return

        if any(
            x in dirty_fields
            for x in ["version_major", "version_minor", "version_patch"]
        ):
            self.version = (
                f"{self.version_major}.{self.version_minor}.{self.version_patch}"
            )

    def _get_version_parts(self) -> tuple[int, int, int]:
        """
        Parse current version string into integer parts.
        """
        if not self.version:
            return self.DEFAULT_VERSION_PARTS
        try:
            major, minor, patch = map(int, self.version.split("."))
            return major, minor, patch
        except Exception as e:
            raise InvalidVersionException(
                f"Cannot parse version parts from '{self.version}'"
            ) from e

    def bump_version(self, bump_type: str = "patch", commit: bool = True) -> str:
        """
        Bump the semantic version of this instance.

        Args:
            bump_type: Type of version bump ('major', 'minor', or 'patch').
            commit: Whether to save the instance immediately (only if not adding).

        Returns:
            str: The newly bumped version string.
        """
        major = self.version_major if self.version_major is not None else 1
        minor = self.version_minor if self.version_minor is not None else 0
        patch = self.version_patch if self.version_patch is not None else 0

        if bump_type == "patch":
            patch += 1
        elif bump_type == "minor":
            minor += 1
            patch = 0
        elif bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        else:
            raise ValueError(
                f"Invalid bump_type '{bump_type}'. Expected 'major', 'minor', or 'patch'."
            )

        self.version_major = major
        self.version_minor = minor
        self.version_patch = patch
        self.version = f"{major}.{minor}.{patch}"

        if commit and not self._state.adding:
            self.save(
                update_fields=[
                    "version",
                    "version_major",
                    "version_minor",
                    "version_patch",
                ]
            )

        return self.version
