"""
Email backend implementations and delivery adapters.
"""

from .console import CoreConsoleEmailBackend
from .sendgrid import SendGridEmailBackend

__all__ = [
    "CoreConsoleEmailBackend",
    "SendGridEmailBackend",
]
