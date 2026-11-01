"""
DRF serializers for CRM entities and related customer sub-resources.

Provides:
- CustomerSerializer: Standard serializer for creating and updating customer profiles.
- CustomerDetailsSerializer: Comprehensive read-only serializer embedding related contacts and preferences.
- CustomerPhoneSerializer: Serializer for customer phone records.
- CustomerEmailSerializer: Serializer for customer email records.
- CustomerAddressSerializer: Serializer for customer address records.
- CustomerIdentificationSerializer: Serializer for customer KYC and identity documents.
- CustomerPreferenceSerializer: Serializer for individual customer preference values.
- CustomerPreferenceTypeSerializer: Serializer for customer preference definitions and schema choices.
"""

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
    """
    Serialize and validate customer phone numbers.

    Enforces phone format validation and contact type choices.
    """

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
    """
    Serialize and validate customer email addresses.

    Enforces email format validation and contact type choices.
    """

    class Meta:
        model = CustomerEmail
        fields = ["id", "customer", "email", "email_type", "is_primary", "is_verified"]
        read_only_fields = ["id"]


class CustomerAddressSerializer(DynamicReadOnlyModelSerializer):
    """
    Serialize and validate customer physical and mailing addresses.

    Exposes the composite ``full_address`` property as a read-only field.
    """

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
    """
    Serialize customer KYC, identity credentials, and verification status.

    Includes the human-readable ``identity_type_display`` label.
    """

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
    """
    Serialize individual customer preference assignments.

    Includes human-readable code and label sourced from the associated preference type.
    """

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
    """
    Read-only serializer for comprehensive customer profile details.

    Embeds related phone numbers, email addresses, physical addresses,
    KYC identifications, and active preference settings.
    """

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
    """
    Serialize customer preference type schemas and configuration options.
    """

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
    """
    Serialize customer profile attributes for creation and updates.
    """

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
        """
        Create and return a new Customer instance.

        Args:
            validated_data (dict): Validated customer field data.

        Returns:
            Customer: Newly created customer profile instance.
        """
        return super().create(validated_data)
