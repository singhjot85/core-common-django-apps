import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from google.auth.transport._http_client import Request as GoogleAuthRequest
from google.oauth2 import id_token as google_id_token

from core.apps.users.constants import SocialProviderChoices
from core.apps.users.services.social.base import BaseSocialAuthService

LOGGER = logging.getLogger(__name__)


class GoogleAuthService(BaseSocialAuthService):
    """
    Google social authentication provider implementing the BaseSocialAuthService template.
    """

    provider = SocialProviderChoices.GOOGLE

    def verify_token(self, token_str: str) -> dict:
        """
        Verify Google OAuth2 / OIDC ID token.
        TODO: Use encrypted credentials from database instead of plain creds from django-settings.
        """
        try:
            client_id = getattr(settings, "GOOGLE_AUTH_CLIENT_ID", None)
            request = GoogleAuthRequest()
            payload = google_id_token.verify_oauth2_token(token_str, request, client_id)
            return payload
        except Exception as e:
            LOGGER.error(f"Google ID token verification failed: {e}")
            raise ValidationError(_("Invalid Google authentication token.")) from e

    def extract_user_claims(self, payload: dict) -> tuple[str, str, str, str, dict]:
        """Extract Google profile claims."""
        uid = payload.get("sub", "")
        email = payload.get("email", "")
        first_name = payload.get("given_name", "")
        last_name = payload.get("family_name", "")
        extra_data = {
            "email": email,
            "name": payload.get("name"),
            "picture": payload.get("picture"),
        }
        return uid, email, first_name, last_name, extra_data
