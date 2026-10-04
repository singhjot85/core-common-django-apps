from core.apps.crm import models_abstract


class Customer(models_abstract.AbstractCustomer):
    """
    Concrete Customer model.
    """

    class Meta(models_abstract.AbstractCustomer.Meta):
        swappable = "CRM_CUSTOMER_MODEL"


class CustomerPhone(models_abstract.AbstractCustomerPhone):
    """
    Concrete CustomerPhone model.
    """

    class Meta(models_abstract.AbstractCustomerPhone.Meta):
        swappable = "CRM_CUSTOMER_PHONE_MODEL"


class CustomerEmail(models_abstract.AbstractCustomerEmail):
    """
    Concrete CustomerEmail model.
    """

    class Meta(models_abstract.AbstractCustomerEmail.Meta):
        swappable = "CRM_CUSTOMER_EMAIL_MODEL"


class CustomerAddress(models_abstract.AbstractCustomerAddress):
    """
    Concrete CustomerAddress model.
    """

    class Meta(models_abstract.AbstractCustomerAddress.Meta):
        swappable = "CRM_CUSTOMER_ADDRESS_MODEL"


class CustomerIdentification(models_abstract.AbstractCustomerIdentification):
    """
    Concrete CustomerIdentification model.
    """

    class Meta(models_abstract.AbstractCustomerIdentification.Meta):
        swappable = "CRM_CUSTOMER_IDENTIFICATION_MODEL"


class CustomerPreferenceType(models_abstract.AbstractCustomerPreferenceType):
    """
    Concrete CustomerPreferenceType model.
    """

    class Meta(models_abstract.AbstractCustomerPreferenceType.Meta):
        swappable = "CRM_CUSTOMER_PREFERENCE_TYPE_MODEL"


class CustomerPreference(models_abstract.AbstractCustomerPreference):
    """
    Concrete CustomerPreference model.
    """

    class Meta(models_abstract.AbstractCustomerPreference.Meta):
        swappable = "CRM_CUSTOMER_PREFERENCE_MODEL"
