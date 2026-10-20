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
        """Filter out soft-deleted user records by default."""
        return super().get_queryset().filter(is_removed=False)

    def all_objects(self):
        """Include soft-deleted records."""
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
        Wrapper to get_or_create and return a regular User.
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
        Wrapper to get_or_create and return a regular User.
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
        Create and return a regular User.
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
        Create and return a superuser with admin privileges.
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
