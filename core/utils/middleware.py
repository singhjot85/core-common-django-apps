"""
Authentication middleware for core applications.

Provides server-side JWT cookie authentication for Django template views,
populating `request.user` when a valid `access_token` or `core_access_token`
cookie is present.

Also delegates the automatic attachment of JWT cookies on responses generated
by authentication views, and rejects requests containing expired JWT cookies
with HTTP 404 Not Found.
"""

import logging
import time
import typing
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpRequest, HttpResponse, HttpResponseNotFound
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.settings import api_settings as restjwt_settings
from rest_framework_simplejwt.tokens import AccessToken

if typing.TYPE_CHECKING:
    from core.apps.users.models_abstract import AbstractUser

LOGGER = logging.getLogger(__name__)

ACCESS_TOKEN_COOKIE_NAME = getattr(settings, "ACCESS_TOKEN_COOKIE_NAME", "access_token")
REFRESH_TOKEN_COOKIE_NAME = getattr(
    settings, "REFRESH_TOKEN_COOKIE_NAME", "refresh_token"
)


class JWTCookieAuthenticationMiddleware:
    """
    Middleware that authenticates requests containing a valid JWT access token cookie
    and delegates setting auth cookies on outgoing responses.

    Behavior:
    - Inspects incoming requests for ``access_token`` in ``request.COOKIES``.
    - If present, checks remaining lifetime:
        - If still valid, retrieves the active user and attaches to ``request.user``.
        - If expired or invalid (on non-exempt routes), rejects the request with 404 Not Found
          directly from the middleware and clears the expired cookies.
        - On exempt routes (e.g. login/auth endpoints), permits access and clears the expired cookie
          from the client response.
    - On outgoing responses, detects auth tokens (from ``request._auth_tokens`` or ``response.data``)
      and sets ``access_token`` and HttpOnly ``refresh_token`` cookies automatically.
    """

    DEFAULT_EXEMPT_PATHS: tuple[str, ...] = (
        "/login/",
        "/signup/",
        "/register/",
        "/api/users/v1/auth/",
        "/api/v1/auth/",
        "/static/",
        # "/media/",
        # "/set-language/",
        "/favicon.ico",
    )

    def __init__(
        self, get_response: typing.Callable[[HttpRequest], HttpResponse]
    ) -> None:
        """
        Initialize the middleware with the next handler in the chain.

        Args:
            get_response: Next middleware or view handler in the execution chain.
        """
        self.get_response = get_response
        self._user_model = None

    @property
    def user_model(self) -> type["AbstractUser"]:
        """
        Lazily resolve and cache the active User model once per middleware instance.

        Returns:
            type[Model]: Resolved Django User model class.
        """
        if self._user_model is None:
            self._user_model = get_user_model()
        return self._user_model

    @classmethod
    def is_exempt_path(cls, path: str) -> bool:
        """
        Check if the given request path is exempt from expired token rejection.

        Args:
            path: Incoming request path.

        Returns:
            bool: True if exempt, False otherwise.
        """
        exempt_paths = getattr(
            settings, "JWT_AUTH_EXEMPT_PATHS", cls.DEFAULT_EXEMPT_PATHS
        )
        return any(path.startswith(prefix) for prefix in exempt_paths)

    @classmethod
    def set_auth_cookies(cls, response: HttpResponse, tokens: dict) -> HttpResponse:
        """
        Attach JWT authentication tokens to HTTP response cookies.

        Sets ``access_token`` (readable by client) and HttpOnly ``refresh_token``
        with SameSite=Lax.

        Args:
            response: Outgoing HTTP response.
            tokens: Dictionary containing ``access`` and optionally ``refresh`` and ``access_expires_in``.

        Returns:
            HttpResponse: The modified response with cookie headers.
        """
        if not hasattr(response, "set_cookie"):
            return response

        secure = not getattr(settings, "DEBUG", False)
        if "access" in tokens:
            access_lifetime = getattr(
                restjwt_settings, "ACCESS_TOKEN_LIFETIME", timedelta(minutes=60)
            )
            access_max_age = int(access_lifetime.total_seconds())
            raw_max_age = tokens.get("access_expires_in")
            if raw_max_age:
                try:
                    access_max_age = int(raw_max_age)
                except (ValueError, TypeError):
                    pass

            response.set_cookie(
                key=ACCESS_TOKEN_COOKIE_NAME,
                value=tokens["access"],
                max_age=access_max_age,
                httponly=False,
                samesite="Lax",
                secure=secure,
                path="/",
            )

        if "refresh" in tokens:
            refresh_lifetime = getattr(
                restjwt_settings, "REFRESH_TOKEN_LIFETIME", timedelta(days=2)
            )
            refresh_max_age = int(refresh_lifetime.total_seconds())
            response.set_cookie(
                key=REFRESH_TOKEN_COOKIE_NAME,
                value=tokens["refresh"],
                max_age=refresh_max_age,
                httponly=True,
                samesite="Lax",
                secure=secure,
                path="/",
            )
        return response

    @classmethod
    def clear_auth_cookies(cls, response: HttpResponse) -> HttpResponse:
        """
        Remove authentication cookies from the HTTP response.

        Args:
            response: HTTP response to clear cookies from.

        Returns:
            HttpResponse: Modified response with deletion headers.
        """
        if hasattr(response, "delete_cookie"):
            response.delete_cookie(ACCESS_TOKEN_COOKIE_NAME, path="/")
            response.delete_cookie(REFRESH_TOKEN_COOKIE_NAME, path="/")

        return response

    def _validate_token_and_get_user(self, token: str) -> tuple[bool, typing.Any, bool]:
        """
        Validate JWT access token and retrieve active user instance.

        Args:
            token: Raw JWT access token string.

        Returns:
            tuple[bool, Optional[User], bool]: (is_valid, user_instance, is_expired)
        """
        is_expired = True
        try:
            validated_token = AccessToken(token)
            exp = validated_token.get("exp")
            if exp is not None:
                remaining_seconds = exp - time.time()
                if remaining_seconds <= 0:
                    return False, None, is_expired

            is_expired = False

            # restJWT saves under it under user_id
            user_id = validated_token.get(
                getattr(restjwt_settings, "USER_ID_CLAIM", "user_id")
            )
            if not user_id:
                return False, None, is_expired

            try:
                user = self.user_model.objects.get(pk=user_id, is_active=True)
            except (
                self.user_model.DoesNotExist,
                self.user_model.MultipleObjectsReturned,
            ):
                return False, None, is_expired

            return True, user, is_expired
        except (InvalidToken, TokenError):
            return False, None, is_expired
        except Exception as exc:
            LOGGER.debug("JWT token validation exception: %s", exc)
            return False, None, is_expired

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        Process incoming request and delegate auth cookie attachment on outgoing response.

        Args:
            request: The incoming HTTP request.

        Returns:
            HttpResponse: The response from subsequent middleware or rejected 404 response.
        """
        clear_cookies_on_response = False
        user = getattr(request, "user", None)

        # Authenticate via JWT cookie only if request is not already authenticated
        if not (user and user.is_authenticated):
            token = None
            if hasattr(request, "COOKIES"):
                token = request.COOKIES.get(ACCESS_TOKEN_COOKIE_NAME)

            if token:
                is_valid, authenticated_user, is_expired = (
                    self._validate_token_and_get_user(token)
                )

                if is_valid and authenticated_user:
                    request.user = authenticated_user

                elif is_expired or not is_valid:
                    if not self.is_exempt_path(request.path):
                        LOGGER.debug(
                            "Rejecting request with 404 due to expired/invalid JWT cookie: %s",
                            request.path,
                        )
                        response = HttpResponseNotFound("Resource not found.")
                        return self.clear_auth_cookies(response)
                    else:
                        clear_cookies_on_response = True
                        LOGGER.debug(
                            "Expired JWT cookie encountered on exempt path: %s",
                            request.path,
                        )

        # Execute the view
        response = self.get_response(request)

        # 1. Check if a view explicitly attached tokens to the request object
        tokens = getattr(request, "_auth_tokens", None)

        # 2. If not found on the request, inspect DRF's response payload
        if (
            not tokens
            and isinstance(response, Response)
            and isinstance(response.data, dict)
            and "access" in response.data  # Make sure this is from a auth-view
        ):
            tokens = response.data

        if tokens and isinstance(tokens, dict) and "access" in tokens:
            self.set_auth_cookies(response, tokens)
        elif clear_cookies_on_response:
            self.clear_auth_cookies(response)

        return response
