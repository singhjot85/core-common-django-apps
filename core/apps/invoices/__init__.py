import typing

from django.apps import apps as django_apps
from django.conf import settings

if typing.TYPE_CHECKING:
    from .models_abstract import (
        AbstractBillingOrganization,
        AbstractInvoice,
        AbstractInvoiceAddress,
        AbstractInvoiceItem,
        AbstractInvoiceItemEntry,
        AbstractInvoiceItemFee,
        AbstractInvoiceParty,
        AbstractInvoicePartyCategory,
        AbstractInvoicePartyEmail,
        AbstractInvoicePartyPhone,
        AbstractInvoiceTemplate,
        AbstractOrganizationAssets,
        AbstractOrganizationEmail,
        AbstractOrganizationFinancials,
        AbstractOrganizationPhone,
    )


def get_invoice_model():
    """Get dynamic concrete Invoice model."""
    return typing.cast(
        type["AbstractInvoice"],
        django_apps.get_model(settings.INVOICES_INVOICE_MODEL, require_ready=False),
    )


def get_invoice_address_model():
    """Get dynamic concrete InvoiceAddress model."""
    return typing.cast(
        type["AbstractInvoiceAddress"],
        django_apps.get_model(
            settings.INVOICES_INVOICE_ADDRESS_MODEL, require_ready=False
        ),
    )


def get_invoice_template_model():
    """Get dynamic concrete InvoiceTemplate model."""
    return typing.cast(
        type["AbstractInvoiceTemplate"],
        django_apps.get_model(
            settings.INVOICES_INVOICE_TEMPLATE_MODEL, require_ready=False
        ),
    )


def get_billing_organization_model():
    """Get dynamic concrete BillingOrganization model."""
    return typing.cast(
        type["AbstractBillingOrganization"],
        django_apps.get_model(
            settings.INVOICES_BILLING_ORGANIZATION_MODEL, require_ready=False
        ),
    )


def get_organization_email_model():
    """Get dynamic concrete OrganizationEmail model."""
    return typing.cast(
        type["AbstractOrganizationEmail"],
        django_apps.get_model(
            settings.INVOICES_ORGANIZATION_EMAIL_MODEL, require_ready=False
        ),
    )


def get_organization_phone_model():
    """Get dynamic concrete OrganizationPhone model."""
    return typing.cast(
        type["AbstractOrganizationPhone"],
        django_apps.get_model(
            settings.INVOICES_ORGANIZATION_PHONE_MODEL, require_ready=False
        ),
    )


def get_organization_financials_model():
    """Get dynamic concrete OrganizationFinancials model."""
    return typing.cast(
        type["AbstractOrganizationFinancials"],
        django_apps.get_model(
            settings.INVOICES_ORGANIZATION_FINANCIALS_MODEL, require_ready=False
        ),
    )


def get_organization_assets_model():
    """Get dynamic concrete OrganizationAssets model."""
    return typing.cast(
        type["AbstractOrganizationAssets"],
        django_apps.get_model(
            settings.INVOICES_ORGANIZATION_ASSETS_MODEL, require_ready=False
        ),
    )


def get_invoice_party_model():
    """Get dynamic concrete InvoiceParty model."""
    return typing.cast(
        type["AbstractInvoiceParty"],
        django_apps.get_model(
            settings.INVOICES_INVOICE_PARTY_MODEL, require_ready=False
        ),
    )


def get_invoice_party_category_model():
    """Get dynamic concrete InvoicePartyCategory model."""
    return typing.cast(
        type["AbstractInvoicePartyCategory"],
        django_apps.get_model(
            settings.INVOICES_INVOICE_PARTY_CATEGORY_MODEL, require_ready=False
        ),
    )


def get_invoice_party_email_model():
    """Get dynamic concrete InvoicePartyEmail model."""
    return typing.cast(
        type["AbstractInvoicePartyEmail"],
        django_apps.get_model(
            settings.INVOICES_INVOICE_PARTY_EMAIL_MODEL, require_ready=False
        ),
    )


def get_invoice_party_phone_model():
    """Get dynamic concrete InvoicePartyPhone model."""
    return typing.cast(
        type["AbstractInvoicePartyPhone"],
        django_apps.get_model(
            settings.INVOICES_INVOICE_PARTY_PHONE_MODEL, require_ready=False
        ),
    )


def get_invoice_item_model():
    """Get dynamic concrete InvoiceItem model."""
    return typing.cast(
        type["AbstractInvoiceItem"],
        django_apps.get_model(
            settings.INVOICES_INVOICE_ITEM_MODEL, require_ready=False
        ),
    )


def get_invoice_item_entry_model():
    """Get dynamic concrete InvoiceItemEntry model."""
    return typing.cast(
        type["AbstractInvoiceItemEntry"],
        django_apps.get_model(
            settings.INVOICES_INVOICE_ITEM_ENTRY_MODEL, require_ready=False
        ),
    )


def get_invoice_item_fee_model():
    """Get dynamic concrete InvoiceItemFee model."""
    return typing.cast(
        type["AbstractInvoiceItemFee"],
        django_apps.get_model(
            settings.INVOICES_INVOICE_ITEM_FEE_MODEL, require_ready=False
        ),
    )
