from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _

from core.utils.lazy_objects import LazyDynamicChoiceTypes

InterfaceTypeChoices = LazyDynamicChoiceTypes()


class DefaultConfigurationInterfaceTypeChoices(TextChoices):
    """
    Default configuration Interface choices shipped with core
    """

    UI_CONFIGURATION = "ui_configuration", _("UI Configuration")
