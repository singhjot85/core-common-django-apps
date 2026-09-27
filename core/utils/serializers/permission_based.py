from .base import DynamicReadOnlyModelSerializer


class ConditionalReadOnlySerializer(DynamicReadOnlyModelSerializer):
    """
    Read-only serializer with ability to specify which fields are read-only.

    TODO: Implement this properly, make it permission based not raw ``user.is_staff``.

    Features:
    - Permission Based Readonly
    - Create/Update operations are disabled with clear error messages
    - Works with any model

    Usage:

        >>> class UserSerializer(ConditionalReadOnlySerializer):
        >>>     class Meta:
        >>>         model = User
        >>>         fields = ['id', 'username', 'email', 'password']
        >>>         read_only_fields = ['password'] # Password stays always read-only
        >>>         conditional_read_only = ["email"] # email only visible to admin.
    """

    @property
    def conditional_read_only_fields(self):
        meta = getattr(self, "Meta", None)
        read_only_fields = getattr(meta, "conditional_read_only", [])
        return read_only_fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request")
        is_staff = request and request.user and getattr(request.user, "is_staff", False)

        if is_staff:
            fields = self.conditional_read_only_fields
            for field_name in fields:
                if field_name in self.fields:
                    self.fields[field_name].read_only = False
        else:
            fields = self.conditional_read_only_fields
            for field_name in fields:
                if field_name in self.fields:
                    self.fields[field_name].read_only = True
