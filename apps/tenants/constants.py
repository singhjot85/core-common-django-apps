from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class TenantContactInfoChoices(TextChoices):

    EMAIL = "email", _("Email")
    ADDRESS = "address", _("Address")
    PHONE = "phone", _("phone")
