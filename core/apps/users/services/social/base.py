import abc
import logging
import typing

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from core.apps.users import get_social_account_model, get_user_model

if typing.TYPE_CHECKING:
    from core.apps.users.models_abstract import AbstractUser

LOGGER = logging.getLogger(__name__)

User = get_user_model()
SocialAccount = get_social_account_model()


class BaseSocialAuthService(abc.ABC):
    """
    Template method pattern base class for social identity providers.

    Subclasses must implement:
    - `provider`: Provider identifier string (e.g. 'google')
    - `verify_token(token_str)`: Hook to verify third-party token with IDP.
    - `extract_user_claims(payload)`: Hook to extract normalized claims.
    """

    provider: str

    @abc.abstractmethod
    def verify_token(self, token_str: str) -> dict:
        """
        Verify the third-party authentication token and return decoded payload claims.

        Args:
            token_str (str): ID token or access token from provider.

        Returns:
            dict: Raw claims payload from provider.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def extract_user_claims(self, payload: dict) -> tuple[str, str, str, str, dict]:
        """
        Extract standardized user profile claims from IDP payload.

        Args:
            payload (dict): Raw claims from verify_token.

        Returns:
            tuple[str, str, str, str, dict]: (uid, email, first_name, last_name, extra_data)
        """
        raise NotImplementedError

    def authenticate_or_register(self, token_str: str) -> tuple["AbstractUser", bool]:
        """
        Template method defining social authentication and auto-provisioning:
        1. Verify third-party token via `verify_token`.
        2. Extract normalized claims via `extract_user_claims`.
        3. If SocialAccount exists for provider + uid, return associated user.
        4. If User exists with matching email, link SocialAccount and mark email verified.
        5. If User does not exist, provision new user with unusable password and link SocialAccount.
        6. Return (user, created).
        """
        payload = self.verify_token(token_str)
        uid, email, first_name, last_name, extra_data = self.extract_user_claims(
            payload
        )

        if not uid or not email:
            raise ValidationError(
                _("Incomplete profile data received from authentication provider.")
            )

        clean_email = email.strip().lower()

        # 1. Check if social account already linked
        social_account = (
            SocialAccount.objects.filter(
                provider=self.provider,
                uid=uid,
            )
            .select_related("user")
            .first()
        )

        if social_account and social_account.user:
            return social_account.user, False

        # 2. Check if user with this email already exists
        user = User.objects.filter(email__iexact=clean_email).first()
        created = False

        if not user:
            user = User.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                email=clean_email,
                is_email_verified=True,
            )
            created = True
        else:
            if not user.is_email_verified:
                user.is_email_verified = True
                user.save(update_fields=["is_email_verified", "modified"])

        # Link social account
        SocialAccount.objects.create(
            user=user,
            provider=self.provider,
            uid=uid,
            extra_data=extra_data,
        )

        return user, created
