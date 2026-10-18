from core.apps.users import models_abstract


class User(models_abstract.AbstractUser):
    """
    Concrete User model for core-apps-django.
    """

    class Meta(models_abstract.AbstractUser.Meta):
        swappable = "AUTH_USER_MODEL"


class SocialAccount(models_abstract.AbstractSocialAccount):
    """
    Concrete SocialAccount model linking third-party identity providers to a user.
    """

    class Meta(models_abstract.AbstractSocialAccount.Meta):
        swappable = "USERS_SOCIAL_ACCOUNT_MODEL"


class OTPLog(models_abstract.AbstractOTPLog):
    """
    Concrete OTPLog model for tracking verification attempts and delivery status.
    """

    class Meta(models_abstract.AbstractOTPLog.Meta):
        swappable = "USERS_OTP_LOG_MODEL"
