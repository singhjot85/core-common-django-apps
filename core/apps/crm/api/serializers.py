from rest_framework import serializers

from core.apps.crm.models import (
    Customer,
    CustomerAddress,
    CustomerEmail,
    CustomerIdentification,
    CustomerPhone,
)


class CustomerPhoneSerializer(serializers.ModelSerializer):
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
            "created",
            "modified",
        ]
        read_only_fields = ["id", "created", "modified"]


class CustomerEmailSerializer(serializers.ModelSerializer):
    """Serializer for customer email addresses."""

    class Meta:
        model = CustomerEmail
        fields = [
            "id",
            "customer",
            "email",
            "email_type",
            "is_primary",
            "is_verified",
            "created",
            "modified",
        ]
        read_only_fields = ["id", "created", "modified"]


class CustomerAddressSerializer(serializers.ModelSerializer):
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
            "latitude",
            "longitude",
            "full_address",
            "created",
            "modified",
        ]
        read_only_fields = ["id", "full_address", "created", "modified"]


class CustomerIdentificationSerializer(serializers.ModelSerializer):
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
            "details",
            "created",
            "modified",
        ]
        read_only_fields = ["id", "identity_type_display", "created", "modified"]


class CustomerSerializer(serializers.ModelSerializer):
    """Serializer for customer profiles with nested contacts and addresses."""

    full_name = serializers.CharField(read_only=True)
    phones = CustomerPhoneSerializer(many=True, read_only=True)
    emails = CustomerEmailSerializer(many=True, read_only=True)
    addresses = CustomerAddressSerializer(many=True, read_only=True)
    identifications = CustomerIdentificationSerializer(many=True, read_only=True)

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
            "gender",
            "details",
            "phones",
            "emails",
            "addresses",
            "identifications",
            "created",
            "modified",
        ]
        read_only_fields = [
            "id",
            "full_name",
            "phones",
            "emails",
            "addresses",
            "identifications",
            "created",
            "modified",
        ]
