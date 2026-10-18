import logging

from django.conf import settings
from django.core.mail import send_mail
from django.utils.translation import gettext_lazy as _

from core.apps.users import get_user_model
from core.apps.users.constants import OTPChannelChoices
from core.apps.users.services.otp.base import BaseOTPService

LOGGER = logging.getLogger(__name__)
User = get_user_model()


class EmailOTPService(BaseOTPService):
    """
    Email-based OTP service implementing the BaseOTPService template.
    """

    channel = OTPChannelChoices.EMAIL

    def check_user_exists(self, identifier: str) -> bool:
        """Check if user exists with the given email address."""
        return User.objects.filter(email__iexact=identifier.strip()).exists()

    def deliver(self, identifier: str, code: str, message: str) -> bool:
        """Deliver the OTP code via Django send_mail.

        TODO: Build out email service, that sends email's from template's and effectively.
            Keep swappable backends on that email service.
        """
        subject = str(_("Your Verification Code"))
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "")
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[identifier.strip()],
                fail_silently=False,
            )
            return True
        except Exception as e:
            LOGGER.exception(f"Failed to send OTP email to {identifier}: {e}")
            return False
