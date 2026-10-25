"""
User model managers for user lifecycle management and authentication.

Provides custom user querysets with automatic soft-deletion filtering,
atomic get-or-create logic resilient to concurrent creation races,
and automatic username generation.
"""

import typing

from django.contrib.auth.models import UserManager as DjangoUserManager
from django.db import IntegrityError, models, transaction
from django.utils.translation import gettext_lazy as _

from core.apps.users import app_settings

if typing.TYPE_CHECKING:
    from core.apps.users.models_abstract import AbstractUser


class UserManager(DjangoUserManager):
    """
    Custom user manager providing support for:
    - Automatic username generation when omitted
    - Unusable passwords for OTP/Social-only signups
    - Soft deletion filtering
    """

    def get_queryset(self):
        """
        Return queryset excluding soft-deleted user records.

        Returns:
            QuerySet: Filtered user queryset where ``is_removed`` is False.
        """
        return super().get_queryset().filter(is_removed=False)

    def all_objects(self):
        """
        Return unfiltered queryset including soft-deleted user records.

        Returns:
            QuerySet: Base user queryset without soft-delete filters.
        """
        return super().get_queryset()

    def get_or_create_user(
        self,
        username: typing.Optional[str] = None,
        email: typing.Optional[str] = None,
        phone_number: typing.Optional[str] = None,
        password: typing.Optional[str] = None,
        **extra_fields,
    ) -> tuple[models.Model, bool]:
        """
        Retrieve an existing user by username or atomically create a new one.

        Handles race conditions during concurrent user creation by catching
        ``IntegrityError`` within a savepoint and returning the existing record.

        Side effects:
            - Creates a user record in the database if not found.
            - Hashes password or assigns unusable password.

        Args:
            username (str, optional): Unique username. If omitted, generated automatically.
            email (str, optional): User email address.
            phone_number (str, optional): E.164 formatted phone number.
            password (str, optional): Plaintext password to hash and store.
            **extra_fields: Additional model field values (e.g. first_name, last_name).

        Returns:
            tuple[models.Model, bool]: Tuple of (user_instance, created_flag).
        """
        try:
            return self.get(username=username), False
        except self.model.DoesNotExist:
            pass

        try:
            with transaction.atomic(using=self.db):
                user = self.create_user(
                    username=username, email=email, password=password, **extra_fields
                )
            return user, True
        except IntegrityError:
            # Concurrent create won the race — fetch the existing row.
            return self.get(username=username), False

    def get_or_create_superuser(
        self,
        username: str,
        email: typing.Optional[str] = None,
        password: typing.Optional[str] = None,
        **extra_fields,
    ) -> tuple[models.Model, bool]:
        """
        Retrieve an existing superuser by username or atomically create a new one.

        Enforces ``is_staff=True`` and ``is_superuser=True``. Catches ``IntegrityError``
        arising from concurrent creations and returns the existing user.

        Side effects:
            - Creates a superuser record in the database if not found.
            - Hashes password.

        Args:
            username (str): Unique username.
            email (str, optional): Superuser email address.
            password (str, optional): Plaintext password to hash and store.
            **extra_fields: Additional model field values.

        Returns:
            tuple[models.Model, bool]: Tuple of (user_instance, created_flag).

        Raises:
            ValueError: If ``is_staff`` or ``is_superuser`` is explicitly set to False.
        """
        try:
            return self.get(username=username), False
        except self.model.DoesNotExist:
            pass

        try:
            with transaction.atomic(using=self.db):
                user = self.create_superuser(
                    username=username, email=email, password=password, **extra_fields
                )
            return user, True
        except IntegrityError:
            # Concurrent create won the race — fetch the existing row.
            return self.get(username=username), False

    def create_user(
        self,
        username: typing.Optional[str] = None,
        email: typing.Optional[str] = None,
        phone_number: typing.Optional[str] = None,
        password: typing.Optional[str] = None,
        **extra_fields,
    ) -> "AbstractUser":
        """
        Create and persist a regular user instance.

        If ``username`` is not provided, dynamically generates a unique username using
        ``app_settings.USERNAME_GENERATOR``. If ``password`` is omitted, sets an unusable
        password to support OTP or social-only authentication.

        Side effects:
            - Generates and validates unique username when omitted.
            - Normalizes email address.
            - Hashes password or sets unusable password flag.
            - Inserts a new user record into the database.

        Args:
            username (str, optional): Desired unique username.
            email (str, optional): User email address.
            phone_number (str, optional): User phone number.
            password (str, optional): Plaintext password.
            **extra_fields: Additional model field values.

        Returns:
            AbstractUser: The newly created and saved user instance.
        """
        first_name = extra_fields.get("first_name", "")
        last_name = extra_fields.get("last_name", "")

        # 1. Resolve or generate username
        if not username or not username.strip():
            generator = app_settings.USERNAME_GENERATOR
            username = generator(
                first_name=first_name,
                last_name=last_name,
                email=email or "",
                phone_number=phone_number or "",
            )

        if email:
            email = self.normalize_email(email)

        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        user = self.model(
            username=username,
            email=email,
            phone_number=phone_number,
            **extra_fields,
        )

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        username: str,
        email: typing.Optional[str] = None,
        password: typing.Optional[str] = None,
        **extra_fields,
    ) -> "AbstractUser":
        """
        Create and persist a superuser with full administrative privileges.

        Ensures ``is_staff`` and ``is_superuser`` are set to True before saving.

        Side effects:
            - Inserts a new superuser record into the database.
            - Hashes the superuser password.

        Args:
            username (str): Unique username.
            email (str, optional): Superuser email address.
            password (str, optional): Plaintext password.
            **extra_fields: Additional model field values.

        Returns:
            AbstractUser: The newly created superuser instance.

        Raises:
            ValueError: If ``is_staff`` or ``is_superuser`` is not True.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(
            username=username,
            email=email,
            password=password,
            **extra_fields,
        )
