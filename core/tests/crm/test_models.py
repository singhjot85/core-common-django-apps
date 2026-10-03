import pytest
from django.contrib.contenttypes.models import ContentType

from core.apps.crm import (
    get_customer_address_model,
    get_customer_email_model,
    get_customer_identification_model,
    get_customer_model,
    get_customer_phone_model,
)
from core.apps.crm.constants import (
    ContactTypeChoices,
    CustomerTypeChoices,
    IdentityTypeChoices,
)

Customer = get_customer_model()
CustomerPhone = get_customer_phone_model()
CustomerEmail = get_customer_email_model()
CustomerAddress = get_customer_address_model()
CustomerIdentification = get_customer_identification_model()


class TestCRMModelUnits:
    """In-memory unit tests for CRM and party model attributes."""

    def test_party_full_name_individual(self):
        """Test full_name formatting for individuals with suffix."""
        customer = Customer(
            first_name="John",
            middle_name="Robert",
            last_name="Doe",
            suffix="Jr.",
            customer_type=CustomerTypeChoices.INDIVIDUAL,
        )
        assert customer.full_name == "John Robert Doe Jr."

    def test_party_full_name_without_suffix(self):
        """Test full_name formatting for individuals without suffix."""
        customer = Customer(
            first_name="John",
            last_name="Doe",
            customer_type=CustomerTypeChoices.INDIVIDUAL,
        )
        assert customer.full_name == "John Doe"

    def test_party_full_name_business(self):
        """Test full_name fallback to business_name."""
        customer = Customer(
            business_name="Acme Corporation",
            customer_type=CustomerTypeChoices.BUSINESS,
        )
        assert customer.full_name == "Acme Corporation"

    def test_party_full_name_empty(self):
        """Test full_name when no name fields are provided."""
        customer = Customer()
        assert customer.full_name == ""

    def test_abstract_address_full_address(self):
        """Test full_address formatting from composite address fields."""
        address = CustomerAddress(
            address_line_1="123 Tech Street",
            address_line_2="Suite 400",
            landmark="Near Central Park",
            city="Bengaluru",
            state="Karnataka",
            postal_code="560001",
            country="IN",
        )
        assert (
            address.full_address
            == "123 Tech Street, Suite 400, Near Central Park, Bengaluru, Karnataka, 560001, IN"
        )


@pytest.mark.django_db
class TestCRMModelsDB:
    """Database integration tests for CRM models and managers."""

    def test_customer_phone_primary_manager(self):
        """Test get_primary and set_primary on CustomerPhone manager."""
        customer = Customer.objects.create(first_name="Alice", last_name="Smith")
        phone1 = CustomerPhone.objects.create(
            customer=customer,
            phone="+919876543210",
            phone_type=ContactTypeChoices.PRIMARY,
            is_primary=True,
        )
        phone2 = CustomerPhone.objects.create(
            customer=customer,
            phone="+919123456780",
            phone_type=ContactTypeChoices.WORK,
            is_primary=False,
        )

        assert CustomerPhone.objects.get_primary(customer) == phone1
        assert customer.primary_phone == phone1

        # Switch primary using manager
        CustomerPhone.objects.set_primary(phone2)
        phone1.refresh_from_db()
        phone2.refresh_from_db()

        assert phone2.is_primary is True
        assert phone1.is_primary is False
        assert CustomerPhone.objects.get_primary(customer) == phone2
        assert customer.primary_phone == phone2

    def test_customer_email_primary_manager(self):
        """Test get_primary and primary toggle on CustomerEmail save."""
        customer = Customer.objects.create(first_name="Bob", last_name="Smith")
        email1 = CustomerEmail.objects.create(
            customer=customer,
            email="bob.primary@example.com",
            is_primary=True,
        )
        email2 = CustomerEmail.objects.create(
            customer=customer,
            email="bob.work@example.com",
            is_primary=False,
        )

        assert CustomerEmail.objects.get_primary(customer) == email1
        assert customer.primary_email == email1

        # Creating a 3rd email with is_primary=True automatically unsets previous
        email3 = CustomerEmail.objects.create(
            customer=customer,
            email="bob.new@example.com",
            is_primary=True,
        )
        email1.refresh_from_db()
        email2.refresh_from_db()

        assert email3.is_primary is True
        assert email1.is_primary is False
        assert email2.is_primary is False
        assert CustomerEmail.objects.get_primary(customer) == email3

    def test_customer_address_primary_manager(self):
        """Test get_primary and set_primary on CustomerAddress manager."""
        customer = Customer.objects.create(first_name="Charlie", last_name="Brown")
        addr1 = CustomerAddress.objects.create(
            customer=customer,
            address_line_1="Addr 1",
            is_primary=True,
        )
        addr2 = CustomerAddress.objects.create(
            customer=customer,
            address_line_1="Addr 2",
            is_primary=False,
        )

        assert CustomerAddress.objects.get_primary(customer) == addr1
        assert customer.primary_address == addr1

        CustomerAddress.objects.set_primary(addr2.id)
        addr1.refresh_from_db()
        addr2.refresh_from_db()

        assert addr2.is_primary is True
        assert addr1.is_primary is False
        assert CustomerAddress.objects.get_primary(customer) == addr2

    def test_customer_identification_gfk(self):
        """Test GenericForeignKey linking on CustomerIdentification."""
        customer = Customer.objects.create(first_name="Diana", last_name="Prince")
        customer_ct = ContentType.objects.get_for_model(Customer)

        ident = CustomerIdentification.objects.create(
            customer=customer,
            identity_type=IdentityTypeChoices.AADHAAR,
            identity_number="1234-5678-9012",
            content_type=customer_ct,
            object_id=str(customer.pk),
            is_verified=True,
        )

        assert ident.customer_identity == customer
        assert str(ident) == f"Aadhaar Card: 1234-5678-9012 ({customer})"

    def test_customer_soft_delete(self):
        """Test soft deletion and exclusion from available_objects."""
        customer = Customer.objects.create(first_name="Eve", last_name="Johnson")
        cust_id = customer.id

        assert Customer.available_objects.filter(id=cust_id).exists()

        customer.delete()

        assert not Customer.available_objects.filter(id=cust_id).exists()
        assert Customer.all_objects.filter(id=cust_id).exists()

        customer.refresh_from_db()
        assert customer.is_removed is True
