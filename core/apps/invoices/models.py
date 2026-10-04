from core.apps.invoices import models_abstract


class Invoice(models_abstract.AbstractInvoice):
    """Concrete Invoice model."""

    class Meta(models_abstract.AbstractInvoice.Meta):
        swappable = "INVOICES_INVOICE_MODEL"


class InvoiceAddress(models_abstract.AbstractInvoiceAddress):
    """Concrete InvoiceAddress model."""

    class Meta(models_abstract.AbstractInvoiceAddress.Meta):
        swappable = "INVOICES_INVOICE_ADDRESS_MODEL"


class InvoiceTemplate(models_abstract.AbstractInvoiceTemplate):
    """Concrete InvoiceTemplate model."""

    class Meta(models_abstract.AbstractInvoiceTemplate.Meta):
        swappable = "INVOICES_INVOICE_TEMPLATE_MODEL"


class BillingOrganization(models_abstract.AbstractBillingOrganization):
    """Concrete BillingOrganization model."""

    class Meta(models_abstract.AbstractBillingOrganization.Meta):
        swappable = "INVOICES_BILLING_ORGANIZATION_MODEL"


class OrganizationEmail(models_abstract.AbstractOrganizationEmail):
    """Concrete OrganizationEmail model."""

    class Meta(models_abstract.AbstractOrganizationEmail.Meta):
        swappable = "INVOICES_ORGANIZATION_EMAIL_MODEL"


class OrganizationPhone(models_abstract.AbstractOrganizationPhone):
    """Concrete OrganizationPhone model."""

    class Meta(models_abstract.AbstractOrganizationPhone.Meta):
        swappable = "INVOICES_ORGANIZATION_PHONE_MODEL"


class OrganizationFinancials(models_abstract.AbstractOrganizationFinancials):
    """Concrete OrganizationFinancials model."""

    class Meta(models_abstract.AbstractOrganizationFinancials.Meta):
        swappable = "INVOICES_ORGANIZATION_FINANCIALS_MODEL"


class OrganizationAssets(models_abstract.AbstractOrganizationAssets):
    """Concrete OrganizationAssets model."""

    class Meta(models_abstract.AbstractOrganizationAssets.Meta):
        swappable = "INVOICES_ORGANIZATION_ASSETS_MODEL"


class InvoicePartyCategory(models_abstract.AbstractInvoicePartyCategory):
    """Concrete InvoicePartyCategory model."""

    class Meta(models_abstract.AbstractInvoicePartyCategory.Meta):
        swappable = "INVOICES_INVOICE_PARTY_CATEGORY_MODEL"


class InvoiceParty(models_abstract.AbstractInvoiceParty):
    """Concrete InvoiceParty model."""

    class Meta(models_abstract.AbstractInvoiceParty.Meta):
        swappable = "INVOICES_INVOICE_PARTY_MODEL"


class InvoicePartyEmail(models_abstract.AbstractInvoicePartyEmail):
    """Concrete InvoicePartyEmail model."""

    class Meta(models_abstract.AbstractInvoicePartyEmail.Meta):
        swappable = "INVOICES_INVOICE_PARTY_EMAIL_MODEL"


class InvoicePartyPhone(models_abstract.AbstractInvoicePartyPhone):
    """Concrete InvoicePartyPhone model."""

    class Meta(models_abstract.AbstractInvoicePartyPhone.Meta):
        swappable = "INVOICES_INVOICE_PARTY_PHONE_MODEL"


class InvoiceItem(models_abstract.AbstractInvoiceItem):
    """Concrete InvoiceItem model."""

    class Meta(models_abstract.AbstractInvoiceItem.Meta):
        swappable = "INVOICES_INVOICE_ITEM_MODEL"


class InvoiceItemEntry(models_abstract.AbstractInvoiceItemEntry):
    """Concrete InvoiceItemEntry model."""

    class Meta(models_abstract.AbstractInvoiceItemEntry.Meta):
        swappable = "INVOICES_INVOICE_ITEM_ENTRY_MODEL"


class InvoiceItemFee(models_abstract.AbstractInvoiceItemFee):
    """Concrete InvoiceItemFee model."""

    class Meta(models_abstract.AbstractInvoiceItemFee.Meta):
        swappable = "INVOICES_INVOICE_ITEM_FEE_MODEL"
