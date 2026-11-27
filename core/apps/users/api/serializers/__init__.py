"""
Serializer exports for the users application authentication and registration domain.

Exposes:
- UserDetailsSerializer, BaseSignupSerializer, BaseOTPVerificationSerializer
- PasswordLoginSerializer, PasswordSignupSerializer
- EmailOTPSendSerializer, EmailOTPLoginSerializer, EmailOTPSignupSerializer
- PhoneOTPSendSerializer, PhoneOTPLoginSerializer, PhoneOTPSignupSerializer
- OTPSendSerializer, OTPVerifySerializer, GoogleLoginSerializer
"""

from .base import (
    BaseOTPVerificationSerializer,
    BaseSignupSerializer,
    UserDetailsSerializer,
)
from .common import (
    GoogleLoginSerializer,
    OTPSendSerializer,
    OTPVerifySerializer,
)
from .email_auth import (
    EmailOTPLoginSerializer,
    EmailOTPSendSerializer,
    EmailOTPSignupSerializer,
)
from .password_auth import (
    PasswordLoginSerializer,
    PasswordSignupSerializer,
)
from .sms_auth import (
    PhoneOTPLoginSerializer,
    PhoneOTPSendSerializer,
    PhoneOTPSignupSerializer,
)

__all__ = [
    "BaseOTPVerificationSerializer",
    "BaseSignupSerializer",
    "EmailOTPLoginSerializer",
    "EmailOTPSendSerializer",
    "EmailOTPSignupSerializer",
    "GoogleLoginSerializer",
    "OTPSendSerializer",
    "OTPVerifySerializer",
    "PasswordLoginSerializer",
    "PasswordSignupSerializer",
    "PhoneOTPLoginSerializer",
    "PhoneOTPSendSerializer",
    "PhoneOTPSignupSerializer",
    "UserDetailsSerializer",
]
