"""
Model factories for the users application.
"""

import factory

from core.apps.users import (
    get_otp_log_model,
    get_social_account_model,
    get_user_model,
)
from core.apps.users.constants import (
    OTPChannelChoices,
    OTPDeliveryStatusChoices,
    OTPPurposeChoices,
    SocialProviderChoices,
)

User = get_user_model()
SocialAccount = get_social_account_model()
OTPLog = get_otp_log_model()


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for generating User instances with standard test password."""

    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.Sequence(lambda n: f"user_{n}@example.com")
    phone_number = factory.Sequence(lambda n: f"+1555000{n:04d}")
    is_active = True
    is_staff = False
    is_superuser = False

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        """Set password using Django's password hasher."""
        raw_password = extracted if extracted is not None else "password123"
        self.set_password(raw_password)
        if create:
            self.save(update_fields=["password"])


class SocialAccountFactory(factory.django.DjangoModelFactory):
    """Factory for generating SocialAccount links."""

    class Meta:
        model = SocialAccount

    user = factory.SubFactory(UserFactory)
    provider = SocialProviderChoices.GOOGLE
    uid = factory.Sequence(lambda n: f"google-uid-{n}")


class OTPLogFactory(factory.django.DjangoModelFactory):
    """Factory for generating OTP audit log records."""

    class Meta:
        model = OTPLog

    recipient = factory.Sequence(lambda n: f"user{n}@example.com")
    channel = OTPChannelChoices.EMAIL
    purpose = OTPPurposeChoices.LOGIN
    status = OTPDeliveryStatusChoices.PENDING
    reference_id = factory.Sequence(lambda n: f"ref_{n}")
