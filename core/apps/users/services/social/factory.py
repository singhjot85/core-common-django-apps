import typing

from core.apps.users.constants import SocialProviderChoices
from core.apps.users.services.social.base import BaseSocialAuthService
from core.apps.users.services.social.google import GoogleAuthService

if typing.TYPE_CHECKING:
    from core.apps.users.models_abstract import AbstractUser


class SocialAuthServiceFactory:
    """
    Factory to retrieve appropriate social authentication service based on provider.
    """

    _registry: dict[str, type[BaseSocialAuthService]] = {
        SocialProviderChoices.GOOGLE: GoogleAuthService,
    }

    @classmethod
    def get_service(cls, provider: str) -> BaseSocialAuthService:
        """
        Instantiate and return the BaseSocialAuthService subclass for the given provider.

        Args:
            provider (str): Social provider identifier (e.g. 'google').

        Returns:
            BaseSocialAuthService: Service instance.
        """
        service_cls = cls._registry.get(provider.lower())
        if not service_cls:
            raise ValueError(f"Unsupported social auth provider: {provider}")
        return service_cls()

    @classmethod
    def authenticate_or_register(
        cls, provider: str, token_str: str
    ) -> tuple["AbstractUser", bool]:
        """
        Convenience dispatcher to authenticate or register user via designated provider.
        """
        service = cls.get_service(provider)
        return service.authenticate_or_register(token_str=token_str)
