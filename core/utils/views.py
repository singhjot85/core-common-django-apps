from django.conf import settings
from django.urls import NoReverseMatch, reverse
from django.views.generic.base import TemplateView

from core.utils.labels import resolve_labels


def _safe_reverse(viewname: str, fallback: str) -> str:
    """
    Safely reverse a URL name or return a fallback path if resolution fails.

    Args:
        viewname: Django URL pattern name.
        fallback: Fallback URL string.

    Returns:
        Reversed URL string or fallback.
    """
    try:
        return reverse(viewname)
    except NoReverseMatch:
        return fallback


class BaseTemplateView(TemplateView):
    """ """

    template_name = None
    template_label_interface_type: str = "users_template_label"
    labels: dict = None

    # Default url-action mapping shipped with each template
    DEFAULT_URL_ACTION_MAP: dict[str, tuple] = {
        "login_action": ("user-login", "/api/users/v1/auth/login/"),
        "signup_action": ("user-signup", "/api/users/v1/auth/signup/"),
        "otp_send_action": ("otp-send", "/api/users/v1/auth/otp/send/"),
        "otp_verify_action": ("otp-verify", "/api/users/v1/auth/otp/verify/"),
        "forgot_password_action": (
            "password-reset",
            "/api/users/v1/auth/password/reset/",
        ),
    }

    # Additional mapping that a subclass wants to use
    URL_ACTION_MAP: dict = None

    def add_url_context(self, social_urls: bool, context: dict):
        """
        Set of urls to be present in all templates
        """
        # Update default url mappings to context data
        for key, val in self.DEFAULT_URL_ACTION_MAP.items():
            context.setdefault(key, _safe_reverse(*val))

        if self.URL_ACTION_MAP:
            # Update additional url mappings to context data
            for key, val in self.URL_ACTION_MAP.items():
                context.setdefault(key, _safe_reverse(*val))

        # Social SSO URLs
        if social_urls:
            context.setdefault(
                "sso_google_url",
                _safe_reverse(
                    "social-google-login", "/api/users/v1/auth/social/google/"
                ),
            )
            context.setdefault("sso_apple_url", "#apple")
            context.setdefault("sso_meta_url", "#meta")

    def add_branding_context(self, context: dict):
        """ """
        context.setdefault(
            "PROJECT_LABEL", getattr(settings, "PROJECT_LABEL", "[Project Label]")
        )
        context.setdefault("brand_logo_url", getattr(settings, "BRAND_LOGO_URL", None))

    def add_routing_context(self, context: dict):
        """
        Add UI side routing context, for swappable UI pages
        """
        # Legal & Status URLs
        context.setdefault("login_url", _safe_reverse("ui-login", "/#/login/"))
        context.setdefault("signup_url", _safe_reverse("ui-signup", "/#/signup/"))
        context.setdefault(
            "forgot_password_url",
            _safe_reverse("ui-forgot-password", "/#/forgot-password/"),
        )

        context.setdefault("privacy_url", getattr(settings, "PRIVACY_URL", "#privacy"))
        context.setdefault("terms_url", getattr(settings, "TERMS_URL", "#terms"))
        context.setdefault("status_url", getattr(settings, "STATUS_URL", "#status"))

    def add_labels_context(self, context: dict):
        """
        Inject template labels from database configuration with backend overrides.
        """
        backend_labels = context.get("labels") or self.labels
        context["labels"] = resolve_labels(
            backend_labels=backend_labels,
            interface_type=self.template_label_interface_type,
        )

    def get_context_data(self, social_urls: bool = False, **kwargs):
        """ """
        context = super().get_context_data(**kwargs)

        self.add_url_context(social_urls, context)
        self.add_branding_context(context)
        self.add_routing_context(context)
        self.add_labels_context(context)

        return context
