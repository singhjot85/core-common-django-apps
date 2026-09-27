import typing

from django.db import models
from rest_framework import serializers
from rest_framework.exceptions import MethodNotAllowed


class ReadOnlyModelSerializer(serializers.ModelSerializer):
    """
    A truly read-only model serializer.

    Features:
    - All fields are automatically read-only
    - Create/Update operations are disabled with clear error messages
    - Works with any model

    Usage:

        >>> class UserSerializer(ReadOnlyModelSerializer):
        >>>     class Meta:
        >>>         model = User
        >>>         fields = ['id', 'username', 'email']  # Or "__all__"
    """

    def __init__(self, *args, **kwargs):
        """Initialize and make all fields read-only."""
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field: serializers.Field
            field.read_only = True

    def create(self, validated_data: dict) -> typing.Any:
        """Disable creation with clear error message."""
        raise MethodNotAllowed(
            method="POST", detail="Create operations are not permitted."
        )

    def update(self, instance: models.Model, validated_data: dict) -> typing.Any:
        """Disable updates with clear error message."""
        raise MethodNotAllowed(
            method="PUT/PATCH", detail="Update operations are not permitted."
        )


class DynamicReadOnlyModelSerializer(ReadOnlyModelSerializer):
    """
    Read-only serializer with ability to specify which fields are read-only.

    Features:
    - Read only fields are dynamically declare-able.
    - Create/Update operations are disabled with clear error messages
    - Works with any model

    Usage:

        >>> class UserSerializer(DynamicReadOnlyModelSerializer):
        >>>     class Meta:
        >>>         model = User
        >>>         fields = ['id', 'username', 'email', 'password']
        >>>         read_only_fields = ['password'] # Password stays read-only
    """

    @property
    def read_only_fields(self):
        meta = getattr(self, "Meta", None)
        read_only_fields = getattr(meta, "read_only_fields", [])
        return read_only_fields

    def __init__(self, *args, **kwargs):
        # Initialize the base ModelSerializer first
        super(ReadOnlyModelSerializer, self).__init__(*args, **kwargs)

        if self.read_only_fields:
            for field_name in self.read_only_fields:
                if field_name in self.fields:
                    self.fields[field_name].read_only = True
        else:
            # If no read_only_fields are specified, behave like a ReadOnlyModelSerializer
            for field in self.fields.values():
                field.read_only = True
