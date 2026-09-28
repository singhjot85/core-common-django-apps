import logging
import typing
from enum import Enum
from functools import cached_property

from constance import config
from django.apps import apps
from django.conf import settings
from django.utils.module_loading import import_string

from core.apps.configurations import get_configuration_model
from core.utils.app_settings.base import (
    AppSettingException,
    BaseDescriptor,
    BaseSettings,
)

# (default, help_text, data-type)
CONSTANCE_CONFIG_ENTRY: typing.TypeAlias = tuple[typing.Any, str, type]

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
            raise RuntimeError("Attribute `name` not found on descriptor")

        settings_key = getattr(self, "app_settings_key", None)
        if not settings_key:
            raise RuntimeError("Attribute `app_settings_key` not found on descriptor")

        prefix = settings_key.removesuffix("_SETTINGS")
        return f"{prefix}_{self.name}".upper()

    def _update_constance_configfieldsets(self):
        """
        Update the ``CONSTANCE_CONFIG_FIELDSETS`` provided by ``django-constances``.

        Example ```CONSTANCE_CONFIG_FIELDSETS```:
        >>> CONSTANCE_CONFIG_FIELDSETS = {
        ...     'General Options': {
        ...         'fields': ('SITE_NAME', 'SITE_DESCRIPTION'),
        ...         'collapse': True
        ...     },
        ...     'Theme Options': ('THEME',),
        ... }

        """
        fieldset_key = getattr(self, "app_settings_key")
        fieldsets = getattr(settings, "CONSTANCE_CONFIG_FIELDSETS", {})

        if not isinstance(fieldsets, dict):
            raise AppSettingException(
                "Malformed CONSTANCE_CONFIG_FIELDSETS", self.app_settings_key
            )

        fieldset_val = fieldsets.get(fieldset_key, None)

        if fieldset_val is None:
            fieldsets[fieldset_key] = {
                "fields": tuple(self.constance_key),
                "collapse": False,
            }

        elif (
            isinstance(fieldset_val, (list, tuple))
            and self.constance_key not in fieldset_val
        ):
            fieldset_val = list(fieldset_val).append(self.constance_key)
            fieldsets[fieldset_key] = tuple(fieldset_val)

        elif isinstance(fieldset_val, dict) and "fields" in fieldset_val:
            fields = fieldset_val["fields"]
            fieldset_val["collapse"] = True
            if isinstance(fields, (list, tuple)) and self.constance_key not in fields:
                fields = list(fields).append(self.constance_key)
                fieldset_val["fields"] = tuple(fields)

        setattr(settings, "CONSTANCE_CONFIG_FIELDSETS", fieldsets)

    def _update_constance_config(self, config_entry: CONSTANCE_CONFIG_ENTRY):
        """
        Update the ``CONSTANCE_CONFIG`` provided by ``django-constances``.
        """
        constance_config = getattr(settings, "CONSTANCE_CONFIG", {})
        constance_config[self.constance_key] = config_entry
        setattr(settings, "CONSTANCE_CONFIG", constance_config)

    def autodiscovery(self, instance: BaseSettings = None):
        """
        AutoDiscover and register constances into django settings and constance settings.
        Adds the constance values to CONSTANCE_CONFIG, and CONSTANCE_CONFIG_FIELDSET / CONSTANCE_CONFIG_FIELDSETS.
        Uses get_raw_value to account for project overrides.
        """
        raw_value = self.get_raw_value(instance)
        config_entry: CONSTANCE_CONFIG_ENTRY = (
            raw_value,
            self.help_text,
            self.data_type,
        )
        self._update_constance_config(config_entry)
        self._update_constance_configfieldsets()

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

    def validate(self, value=None):
        """
        Validate and check if import is valid.
        """
        super().validate(value)

        if value is None:
            value = self.default

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

    def autodiscovery(self, instance: BaseSettings = None):
        """
        Save the given default/raw value to the configuration object in database.
        If config object does not exist for the interface_type, creates it.
        If config object exists, appends that key to details dict if not present.
        Uses get_raw_value to account for project overrides.
        """
        raw_value = self.get_raw_value(instance)
        key = self.name.lower()

        try:
            Configuration = get_configuration_model()
            Configuration.set_config(
                interface_type=self.interface_type,
                details={key: raw_value},
                create_config=True,
                set_cache=False,  # NOTE: This Can cause cache stempede, config will be cached when retrieved
            )
        except Exception as e:
            LOGGER.warning(
                f"Configuration autodiscovery skipped for {self.name} "
                f"({self.interface_type}): {e}"
            )

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
