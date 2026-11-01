from rest_framework import serializers

from core.apps.crm import (
    get_customer_address_model,
    get_customer_email_model,
    get_customer_identification_model,
    get_customer_model,
    get_customer_phone_model,
    get_customer_preference_model,
    get_customer_preference_type_model,
)
from core.utils.serializers import (
    DynamicReadOnlyModelSerializer,
    ReadOnlyModelSerializer,
)

Customer = get_customer_model()
CustomerAddress = get_customer_address_model()
CustomerEmail = get_customer_email_model()
CustomerIdentification = get_customer_identification_model()
CustomerPhone = get_customer_phone_model()
CustomerPreference = get_customer_preference_model()
CustomerPreferenceType = get_customer_preference_type_model()


class CustomerPhoneSerializer(DynamicReadOnlyModelSerializer):
    """Serializer for customer phone numbers."""

    class Meta:
        model = CustomerPhone
        fields = [
            "id",
            "customer",
            "phone",
            "phone_type",
            "is_primary",
            "is_verified",
        ]
        read_only_fields = ["id"]


class CustomerEmailSerializer(DynamicReadOnlyModelSerializer):
    """Serializer for customer email addresses."""

    class Meta:
        model = CustomerEmail
        fields = ["id", "customer", "email", "email_type", "is_primary", "is_verified"]
        read_only_fields = ["id"]


class CustomerAddressSerializer(DynamicReadOnlyModelSerializer):
    """Serializer for customer physical and mailing addresses."""

    full_address = serializers.CharField(read_only=True)

    class Meta:
        model = CustomerAddress
        fields = [
            "id",
            "customer",
            "address_type",
            "is_primary",
            "address_line_1",
            "address_line_2",
            "landmark",
            "city",
            "state",
            "postal_code",
            "country",
            "full_address",
        ]
        read_only_fields = ["id", "full_address"]


class CustomerIdentificationSerializer(DynamicReadOnlyModelSerializer):
    """Serializer for customer KYC and identity documents."""

    identity_type_display = serializers.CharField(
        source="get_identity_type_display", read_only=True
    )

    class Meta:
        model = CustomerIdentification
        fields = [
            "id",
            "customer",
            "identity_type",
            "identity_type_display",
            "identity_number",
            "content_type",
            "object_id",
            "issue_date",
            "expiry_date",
            "issuing_authority",
            "is_verified",
        ]
        read_only_fields = ["id", "identity_type_display"]


class CustomerPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for individual customer preference entries."""

    preference_code = serializers.CharField(
        source="preference_type.code", read_only=True
    )
    preference_label = serializers.CharField(
        source="preference_type.label", read_only=True
    )

    class Meta:
        model = CustomerPreference
        fields = [
            "id",
            "customer",
            "preference_type",
            "preference_code",
            "preference_label",
            "value",
        ]
        read_only_fields = ["id", "preference_code", "preference_label"]


class CustomerDetailsSerializer(ReadOnlyModelSerializer):
    """ """

    full_name = serializers.CharField(read_only=True)
    phones = CustomerPhoneSerializer(many=True, read_only=True)
    emails = CustomerEmailSerializer(many=True, read_only=True)
    addresses = CustomerAddressSerializer(many=True, read_only=True)
    identifications = CustomerIdentificationSerializer(many=True, read_only=True)
    preferences = CustomerPreferenceSerializer(many=True, read_only=True)

    class Meta:
        model = Customer
        fields = [
            "id",
            "suffix",
            "first_name",
            "middle_name",
            "last_name",
            "business_name",
            "full_name",
            "customer_type",
            "status",
            "date_of_birth",
            "phones",
            "emails",
            "addresses",
            "identifications",
            "preferences",
        ]


class CustomerPreferenceTypeSerializer(DynamicReadOnlyModelSerializer):
    """Serializer for customer preference types."""

    data_type_display = serializers.CharField(
        source="get_data_type_display", read_only=True
    )

    class Meta:
        model = CustomerPreferenceType
        fields = [
            "id",
            "code",
            "label",
            "data_type",
            "data_type_display",
            "default_value",
            "values",
            "created",
            "modified",
        ]
        read_only_fields = ["id", "data_type_display", "created", "modified"]


class CustomerSerializer(serializers.ModelSerializer):
    """Serializer for customer profiles with nested contacts and addresses."""

    class Meta:
        model = Customer
        fields = [
            "id",
            "suffix",
            "first_name",
            "middle_name",
            "last_name",
            "business_name",
            "customer_type",
            "status",
            "date_of_birth",
        ]

    def create(self, validated_data):
        return super().create(validated_data)
