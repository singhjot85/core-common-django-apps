from django.db import connection

from core.apps.users.constants import OTPChannelChoices, OTPPurposeChoices
from core.apps.users.services.otp.base import BaseOTPService
from core.apps.users.services.otp.email import EmailOTPService
from core.apps.users.services.otp.sms import PhoneOTPService


class OTPServiceFactory:
    """
    Factory to retrieve appropriate OTP service strategy based on delivery channel.
    """

    _registry: dict[str, type[BaseOTPService]] = {
        OTPChannelChoices.PHONE: PhoneOTPService,
        OTPChannelChoices.EMAIL: EmailOTPService,
    }

    @classmethod
    def get_service(cls, channel: str) -> BaseOTPService:
        """
        Instantiate and return the BaseOTPService subclass for the given channel.

        Args:
            channel (str): Delivery channel (e.g. 'phone' or 'email').

        Returns:
            BaseOTPService: Service instance.
        """
        service_cls = cls._registry.get(channel.lower())
        if not service_cls:
            raise ValueError(f"Unsupported OTP delivery channel: {channel}")
        return service_cls()

    @classmethod
    def send_otp(
        cls,
        identifier: str,
        channel: str,
        purpose: str = OTPPurposeChoices.LOGIN,
    ) -> bool:
        """
        Convenience dispatcher to instantiate service and dispatch OTP.
        """
        service = cls.get_service(channel)
        return service.send_otp(identifier=identifier, purpose=purpose)

    @classmethod
    def verify_otp(cls, identifier: str, code: str) -> tuple[bool, str]:
        """
        Verify the provided OTP against cache.
        """
        return BaseOTPService.verify_otp(identifier=identifier, code=code)

    @classmethod
    def cache_lock_key(cls, identifier: str) -> str:
        """
        Generate a unique cache key for locking OTP operations for a given identifier.

        Args:
            identifier (str): User identifier (phone/email).

        Returns:
            str: Cache key for locking.
        """
        return f"{connection.schema_name}:otp_lock:{identifier}"
