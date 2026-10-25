from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _

from core.utils.lazy_objects import LazyDynamicChoiceTypes

InterfaceTypeChoices = LazyDynamicChoiceTypes()


def get_interface_type_choices():
    """
    Return dynamic choices from InterfaceTypeChoices for model fields.
    """
    return InterfaceTypeChoices.choices


class DefaultConfigurationInterfaceTypeChoices(TextChoices):
    """
    Default configuration Interface choices shipped with core
    """

    UI_CONFIGURATION = "ui_configuration", _("UI Configuration")
    USERS_TEMPLATE_LABEL = "users_template_label", _("Users Template Label")
