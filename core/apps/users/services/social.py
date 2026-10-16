import logging
import typing

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

LOGGER = logging.getLogger(__name__)


class GoogleAuthService:
    """Service to verify Google ID tokens and resolve/provision user accounts."""

    @classmethod
    def verify_token(cls, id_token_str: str) -> dict:
        """
        Verify Google ID token and extract claims.
        """
        try:
            from google.auth.transport import requests
            from google.oauth2 import id_token

            client_id = getattr(settings, "GOOGLE_AUTH_CLIENT_ID", None)
            request = requests.Request()
            payload = id_token.verify_oauth2_token(id_token_str, request, client_id)
            return payload
        except Exception as e:
            LOGGER.error(f"Google ID token verification failed: {e}")
            raise ValidationError(_("Invalid Google authentication token.")) from e

    @classmethod
    def authenticate_or_register(cls, id_token_str: str) -> tuple[typing.Any, bool]:
        """
        Authenticate an existing user or register a new user from Google credentials.
        Returns (user, created).
        """
        from core.apps.users import get_social_account_model, get_user_model
        from core.apps.users.constants import SocialProviderChoices

        payload = cls.verify_token(id_token_str)
        google_sub = payload.get("sub")
        email = payload.get("email")

        if not google_sub or not email:
            raise ValidationError(_("Incomplete profile data received from Google."))

        User = get_user_model()
        SocialAccount = get_social_account_model()

        # 1. Check if social account already linked
        social_account = (
            SocialAccount.objects.filter(
                provider=SocialProviderChoices.GOOGLE,
                uid=google_sub,
            )
            .select_related("user")
            .first()
        )

        if social_account and social_account.user:
            return social_account.user, False

        # 2. Check if user with this email already exists
        user = User.objects.filter(email__iexact=email.strip()).first()
        created = False

        if not user:
            first_name = payload.get("given_name", "")
            last_name = payload.get("family_name", "")
            user = User.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                email=email.strip().lower(),
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
            provider=SocialProviderChoices.GOOGLE,
            uid=google_sub,
            extra_data={
                "email": email,
                "name": payload.get("name"),
                "picture": payload.get("picture"),
            },
        )

        return user, created
