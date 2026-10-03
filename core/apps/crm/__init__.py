import typing

from django.apps import apps as django_apps
from django.conf import settings

if typing.TYPE_CHECKING:
    from .models_abstract import (
        AbstractCustomer,
        AbstractCustomerAddress,
        AbstractCustomerEmail,
        AbstractCustomerIdentification,
        AbstractCustomerPhone,
    )


def get_customer_model():
    """
    Get customer model.
    """
    return typing.cast(
        type["AbstractCustomer"],
        django_apps.get_model(settings.CRM_CUSTOMER_MODEL, require_ready=False),
    )


def get_customer_phone_model():
    """
    Get customer phone model.
    """
    return typing.cast(
        type["AbstractCustomerPhone"],
        django_apps.get_model(settings.CRM_CUSTOMER_PHONE_MODEL, require_ready=False),
    )


def get_customer_email_model():
    """
    Get customer email model.
    """
    return typing.cast(
        type["AbstractCustomerEmail"],
        django_apps.get_model(settings.CRM_CUSTOMER_EMAIL_MODEL, require_ready=False),
    )


def get_customer_address_model():
    """
    Get customer address model.
    """
    return typing.cast(
        type["AbstractCustomerAddress"],
        django_apps.get_model(settings.CRM_CUSTOMER_ADDRESS_MODEL, require_ready=False),
    )


def get_customer_identification_model():
    """
    Get customer identification model.
    """
    return typing.cast(
        type["AbstractCustomerIdentification"],
        django_apps.get_model(
            settings.CRM_CUSTOMER_IDENTIFICATION_MODEL, require_ready=False
        ),
    )
