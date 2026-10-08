import typing

from core.exceptions import RegistryException
from core.utils.registry.base import BaseRegistry


class ClassRegistry(BaseRegistry):

    def __init__(self):
        self._registry = {}

    def register(self, cls: typing.Any, key: str = None):
        """Reigster the class from registry
        Args:
            cls (Any): Class which you want to register.
            key (str, optional): Key corresponding to which the class should register.

        Raises:
            RegistryException
            ValueError
            RegistryException
        """
        if not key and hasattr(cls, "REGISTERY_KEY"):
            if key and not isinstance(key, str):
                raise RegistryException from None

            key = getattr(cls, "REGISTERY_KEY")

        if not key:
            raise ValueError(
                "Registry Key missing, either provide one during registration, or add REGISTERY_KEY as class attribute"
            )

        if key in self._registry:
            if self._registry[key] is cls:
                return
            raise RegistryException(
                f"Key: [{key}] is already registered for [{self._registry[key].__name__}] class"
            )

        self._registry[key] = cls

    def unregister(self, key: str):
        """
        Unreigster the class from registry
        Args:
            key (str): Key corresponding to which the class is registerd
        """
        self._registry.pop(key, None)

    @property
    def registry(self) -> dict:
        """Current Active Registry and all its values"""
        if hasattr(self, "_registry"):
            return self._registry

        return None

    def get(self, key: str) -> typing.Any:
        """
        Get a class corresponding to registry,
        NOTE: Registry only returns a class, object you have to initiate yourself
            Ex:
            >>> some_class = some_registry.get("some_class")
            >>> object = some_class()
            >>> object.do_something()

        Args:
            key (str): Key corresponding to which the class is registerd

        Raises:
            RegistryException
        """
        if key and not isinstance(key, str):
            raise RegistryException from None

        return self._registry.get(key)


class UnorderedClassRegistry(BaseRegistry):

    def __init__(self):
        self._registry = set()

    @property
    def registry(self):
        if hasattr(self, "_registry"):
            return self._registry

        return None

    def contains(self, name: str, raise_exception: bool = False):
        """
        Checks if given name is present in registry

        Args:
            name (str): Name to check in registry.
            raise_exception (bool): Raise exception if not found.
        """
        for kls in self._registry:
            if kls.__name__.lower() == name.lower():
                return True

        if raise_exception:
            raise RegistryException(f"{name} not found in registry.")

    def register(self, kls: typing.Any):
        """
        Register a Class to the Registry

        Args:
            kls: Class that needs to be registered.
        """

        if kls in self._registry:
            return

        self._registry.add(kls)

    def unregister(self, kls: typing.Any):
        """
        Un-Register a Class to the Registry

        Args:
            kls: Class that needs to be un-registered.
        """

        if kls in self._registry:
            self._registry.pop(kls)


def auto_register(registry: type[BaseRegistry], *args, **kwargs):
    """Auto Register you'r classes.

    Args:
        registry: (RegistryType): Registry in which you want the class to be registered.

    Example Usage:
        >>> @auto_register(unordered_class_registry)
        >>> class SomeClasstoRegister(...):
        >>>     ...

        >>> @auto_register(class_registry, key="some_class")
        >>> class SomeClasstoRegister(...):
        >>>     ...

        >>> @auto_register(class_registry, "some_class")
        >>> class SomeClasstoRegister(...):
        >>>     ...

    """

    def decorator(cls):

        if not isinstance(registry, BaseRegistry):
            raise RegistryException(
                f"{registry.__class__.__name__} is not a valid registry."
            )

        registry.register(cls, *args, **kwargs)

        return cls

    return decorator
