import abc
import typing

RegistryType: typing.TypeAlias = typing.Optional[typing.Union[str, dict]]


class BaseRegistry(abc.ABC):
    """Base Implementation of any type of registry"""

    _registry: RegistryType

    @abc.abstractmethod
    def register(self, *args, **kwargs):
        """Implementation to register something in registry"""
        pass

    @abc.abstractmethod
    def unregister(self, *args, **kwargs):
        """Implementation to un-register something from registry"""
        pass
