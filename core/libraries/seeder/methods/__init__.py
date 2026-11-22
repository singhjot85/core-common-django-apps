"""
Method strategies for database seeders.
"""

from core.libraries.seeder.methods.base import BaseObjectMethods
from core.libraries.seeder.methods.defaults import (
    CreateObject,
    GetorCreateObject,
    UpdateOrCreateObject,
)

__all__ = [
    "BaseObjectMethods",
    "CreateObject",
    "GetorCreateObject",
    "UpdateOrCreateObject",
]
