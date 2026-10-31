"""
Serializer exports for the users application authentication and registration domain.

Exposes:
- UserDetailsSerializer, BaseSignupSerializer, BaseOTPVerificationSerializer
- PasswordLoginSerializer, PasswordSignupSerializer
- EmailOTPSendSerializer, EmailOTPLoginSerializer, EmailOTPSignupSerializer
- PhoneOTPSendSerializer, PhoneOTPLoginSerializer, PhoneOTPSignupSerializer
- OTPSendSerializer, OTPVerifySerializer, GoogleLoginSerializer
- Backward-compatible aliases: SignupSerializer, LoginSerializer
"""

from .base import (
    BaseOTPVerificationSerializer as BaseOTPVerificationSerializer,
    BaseSignupSerializer as BaseSignupSerializer,
    UserDetailsSerializer as UserDetailsSerializer,
)
from .common import (
    GoogleLoginSerializer as GoogleLoginSerializer,
    OTPSendSerializer as OTPSendSerializer,
    OTPVerifySerializer as OTPVerifySerializer,
)
from .email_auth import (
    EmailOTPLoginSerializer as EmailOTPLoginSerializer,
    EmailOTPSendSerializer as EmailOTPSendSerializer,
    EmailOTPSignupSerializer as EmailOTPSignupSerializer,
)
from .password_auth import (
    PasswordLoginSerializer as PasswordLoginSerializer,
    PasswordSignupSerializer as PasswordSignupSerializer,
)
from .sms_auth import (
    PhoneOTPLoginSerializer as PhoneOTPLoginSerializer,
    PhoneOTPSendSerializer as PhoneOTPSendSerializer,
    PhoneOTPSignupSerializer as PhoneOTPSignupSerializer,
)

# Aliases for backwards compatibility where generic serializers are referenced
SignupSerializer = PasswordSignupSerializer
LoginSerializer = PasswordLoginSerializer
