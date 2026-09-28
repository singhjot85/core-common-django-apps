import logging
from enum import Enum
from functools import cached_property

from constance import config
from django.apps import apps
from django.utils.module_loading import import_string

from core.apps.configurations import get_configuration_model
from core.utils.app_settings.base import AppSettingException, BaseDescriptor

LOGGER = logging.getLogger(__name__)


class Constance(BaseDescriptor):
    """
    Constance are cached database flags provided by django_constance package.

    Example usage:
    >>> class CRMSettings(...):
    ...     SETTINGS_KEY = "CORE_CRM_SETTINGS"
    ...     FLAG = Constance(...)
    """

    @cached_property
    def constance_key(self):
        """
        Gives the constance key used for the descriptor
        For above example ``flag`` constance key will be ``CORE_CRM_FLAG``.

        So, this can be used to fetch raw constance:
        >>> from constance import config
        ... config.CORE_CRM_FLAG
        """
        if not hasattr(self, "name"):
            raise RuntimeError("Attribte `name` not found on descriptor")

        if not hasattr(self, "app_settings_name"):
            raise RuntimeError("Attribte `app_settings_name` not found on descriptor")

        return f"{self.name.upper()}_{self.app_settings_key.upper()}"

    def autodiscovery(self):
        """
        AutoDiscover and register constances
        """

    def resolve(self, raw_value):
        """
        Resolve Constance, i.e. __get__ for constace returns what
        For constance it try getting the constance value from cache then DB
        """
        constance_value = None

        try:
            constance_value = getattr(config, self.constance_key)

        except RuntimeError as tempExp:
            raise AppSettingException(
                f"Invalid Descriptor: {str(tempExp)}", self.app_settings_key
            ) from tempExp

        except AttributeError as attrError:
            LOGGER.error(
                msg=f"Constance Not found for {self.constance_key}", exc_info=attrError
            )

        except Exception as e:
            raise AppSettingException(str(e), self.app_settings_key) from e

        return constance_value


class SettingsType(Enum):
    """
    Differnt types of settings, django settings are classified into multiple types.
    - Import (Settings can be available at time of __get__).
    - Deffered Import (Setting should be available during descriptor __init__ time).
    """

    IMPORT = "import"
    DEFFERED_IMPORT = "deffered_import"
    MODEL_IMPORT = "model_import"


class Settings(BaseDescriptor):
    """
    Settings are raw django settings, these are not stored in any database
    they come statically from code,
    Settings that should be set as ``Settings``:
    - Settings that should not change after code is shipped.
    - Settings that cannot be changed without code change.

    Ex: Choices, Model, Serializer Class imports, or just a normal True/False flag.
    """

    def validate(self, value):
        """
        Validate and check if import is valid.
        """
        super().validate(value)
        if self.data_type == SettingsType.MODEL_IMPORT.value:
            try:
                apps.get_model(value, require_ready=False)
            except Exception as e:
                raise AppSettingException(str(e), self.app_settings_key) from e

        if self.data_type == SettingsType.DEFFERED_IMPORT.value:
            try:
                import_string(value)
            except Exception as e:
                raise AppSettingException(str(e), self.app_settings_key) from e

    def resolve(self, raw_value):
        """
        Resolve the import value and import the corresponding class
        """
        if self.data_type == SettingsType.MODEL_IMPORT.value:
            return apps.get_model(raw_value, require_ready=True)

        return import_string(raw_value)


class Configuration(BaseDescriptor):
    """
    Configuration Settings to get a json configuration setting from database.
    These Settings contain large mappings that need to be version maintained.
    """

    def __init__(self, default, interface_type: str, data_type, help_text=""):
        """
        Set inteface type on configs descriptor
        """
        self.interface_type = interface_type
        super().__init__(default, data_type, help_text)

    def autodiscovery(self):
        """
        Save the given default value to the configuration object in database
        """

    def resolve(self, raw_value):
        """
        Get Configuration from cache or databse
        """
        Configuration = get_configuration_model()

        try:
            config_details = Configuration.get_configuration(
                interface_type=self.interface_type
            )
            return config_details.get(self.name.lower(), self.default)
        except Exception as e:
            raise AppSettingException(str(e), self.app_settings_key)
