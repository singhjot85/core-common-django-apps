from .base import (
    BaseOTPVerificationSerializer as BaseOTPVerificationSerializer,
    BaseSignupSerializer as BaseSignupSerializer,
    UserDetailsSerializer as UserDetailsSerializer,
)
from .email_auth import (
    EmailOTPLoginSerializer as EmailOTPLoginSerializer,
    EmailOTPSignupSerializer as EmailOTPSignupSerializer,
)
from .password_auth import (
    PasswordLoginSerializer as PasswordLoginSerializer,
    PasswordSignupSerializer as PasswordSignupSerializer,
)
from .sms_auth import (
    PhoneOTPLoginSerializer as PhoneOTPLoginSerializer,
    PhoneOTPSignupSerializer as PhoneOTPSignupSerializer,
)

# Aliases for backwards compatibility where generic serializers are referenced
SignupSerializer = PasswordSignupSerializer
LoginSerializer = PasswordLoginSerializer
