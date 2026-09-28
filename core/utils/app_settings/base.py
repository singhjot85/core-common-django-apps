from __future__ import annotations

import typing

from django.conf import settings

T = typing.TypeVar("T")


class AppSettingException(Exception):
    """
    Exceptions related to app_settings
    """

    def __init__(self, message, setting_label: str = None, *args):
        """Overriding to add setting_label on the exception."""
        if setting_label:
            message = f"[{setting_label}]: {message}"

        super().__init__(message, *args)


class BaseDescriptor:
    """
    Abstract template-pattern descriptor

    Subclass implements `resolve(raw_value)`, this is a template that each descriptor is going to use.
    Override resolution (project_settings.<APP>_APP_SETTINGS -> default) is shared and lives
    here so every subclass gets it for free and consistently.
    """

    name: str  # Name of the settings attribute, Ex: MAX_RETRY_COUNT
    app_settings_key: str  # Name of the settings, Ex: CRMSettings

    def __init__(
        self,
        default: typing.Any,
        data_type: typing.Union[type, list[type]],
        help_text: str = "",
    ):
        """
        Set Descriptor Attributes, each attribute has a different role going forward.

        Args:
            default (typing.Any): Default value of the setting
            help_text (str): Doc string explaining the setting,
                TODO: later will be used in django-admin
            data_type(type): Default class/protocol to type cast the setting
        """
        self.default = default
        self.data_type = data_type
        self.help_text = help_text

        self.validate(self.default)

    def validate(self, value):
        """
        Validate if setting is formed correctly
        """
        from core.utils.error_handling.exceptions import InvalidTypeError

        if not isinstance(value, self.data_type):
            raise InvalidTypeError(type=type(value), expected=type(self.data_type))

    def __set_name__(self, owner: type[BaseSettings], name: str) -> None:
        """
        During Descriptor class name setting, set the parent app_setting name as-well
        """
        self.name = name
        self.app_settings_key = getattr(owner, "SETTINGS_KEY")

    def __set__(self, instance: BaseSettings, value: typing.Any):
        """
        Settings are supposed to be changed at runtime,
        The only settings that suppotr this must, override this method.
        """
        raise AttributeError(
            f"{self.name!r} is read-only. Use project_settings."
            f"{instance.SETTINGS_KEY} or django.test.override_settings "
            f"to vary it, rather than assigning to it directly."
        )

    def __get__(self, instance: BaseSettings, owner: type):
        """
        NOTE: On Class.ATTRIBUTE, instance is none,
            and on object.ATTRIBUTE, instance is object/self.
        """
        if instance is None:
            # Class-level access returns the descriptor itself.
            # Required for introspection: the registry and validation walk descriptors, not resolved values.
            return self

        raw_value = self.get_raw_value(instance)
        value = self.resolve(raw_value)
        self.validate(value)

        return value

    def get_raw_value(self, instance: BaseSettings) -> typing.Any:
        """Get the resolved raw value of a setting, It gives priority to ``django.conf.settings``
        If ``django.conf.settings`` doesn't have this then the default value passed is used.

        This is where ``self.name`` saves us, as it was set using the ``__set_name__``,
        it's always present even before object creation.

        Args:
            instance (BaseSettings): Instance of the Settings class implementing the setting

        Returns:
            resolved raw setting value
        """
        overrides = getattr(settings, instance.SETTINGS_KEY, {})
        return overrides.get(self.name, self.default)

    def resolve(self, raw_value: typing.Any) -> typing.Any:
        """Per-type resolution hook. Must be implemented by subclasses.

        Args:
            raw_value (Any): Raw value that comes from project or app settings.

        Returns:
            resolved setting that ``app_settings.SETTING_NAME`` should return.
        """

        raise NotImplementedError(
            f"resolve not implemented for setting descriptor: {self.__class__.__name__}"
        )


class SettingsMeta(type):
    """
    Metaclass for BaseSettings and all subclasses.

    This metaclass runs at class definition time to:
    1. Process the inner Meta class to determine the app_label/override key
    2. Collect all SettingType descriptors for later enumeration
    """

    @staticmethod
    def build_descriptor_map(kls_attrs: dict) -> dict:
        """Build Decriptors map

        Returns:

            >>> { descriptor_name: descriptor }
        """
        _descriptor_map = {}

        for attr_name, attr_val in kls_attrs.items():
            if isinstance(attr_val, BaseDescriptor):
                _descriptor_map[attr_name] = attr_val

        return _descriptor_map

    def __new__(mcs, name, bases, attrs):
        """
        Oerriding ``__new__`` to return modified instance of class

        This new instance has a compiletime built atrribute on class ``override_settings_name``
        This will be the value that'll be used in ``project_settings`` to override given settings

        Example Usage:

        >>> {
            "OVERRIDE_SETTING_NAME": {
                "SETTING_NAME": Value
            }
        }
        """
        from core.utils.error_handling.exceptions import InvalidTypeError

        # Create the class
        cls: type[BaseSettings] = super().__new__(mcs, name, bases, attrs)

        # Validate if it has a valid settings key
        if not hasattr(cls, "SETTINGS_KEY"):
            raise AppSettingException("SETTINGS_KEY is required to define app_settings")

        settings_key = getattr(cls, "SETTINGS_KEY", None)
        if not isinstance(settings_key, str):
            raise InvalidTypeError(type=type(settings_key), expected=str)
        # TODO: We should add validation to check if the settings key is already used

        cls._descriptors = SettingsMeta.build_descriptor_map(attrs)
        return cls


class BaseSettings(metaclass=SettingsMeta):
    """
    Base class for all app settings classes.

    Subclasses will automatically get:
    1. An override_settings_name based on their Meta.app
    2. A _descriptors dict containing all SettingType descriptors
    """

    # This will be set by the metaclass
    SETTINGS_KEY: str
    _descriptors: dict = {}

    @property
    def override_settings_name(self):
        return self.SETTINGS_KEY

    def __init__(self):
        """
        Validate the descriptors before creating settings instance.
        """
        for descriptor in self._descriptors.values():
            descriptor: BaseDescriptor
            descriptor.validate()

    def raw(self, setting_name: str) -> typing.Any:
        """Get raw value instead of the resolved one for given ``setting_name``<br/>

        Args:
            setting_name (str): Setting Name i.e. the atrribute name.

        Returns:
            raw value set in ``project_settings`` or the default value
        """
        descriptor: BaseDescriptor = self._descriptors.get(setting_name)
        if not descriptor:
            raise AttributeError(f"Setting '{setting_name}' not found")

        return descriptor.get_raw_value(self)

    @classmethod
    def get_descriptors(cls) -> dict:
        """
        Get all SettingType descriptors defined on this settings class.

        Returns:
            dict: Mapping of setting names to their descriptor instances
        """
        return cls._descriptors

    @classmethod
    def get_setting_names(cls) -> list:
        """
        Get the names of all settings defined on this class.

        Returns:
            list: Names of all settings
        """
        return list(cls._descriptors.keys())
