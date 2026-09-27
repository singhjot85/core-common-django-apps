import logging
import typing

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import models
from django.http import HttpRequest
from model_utils.models import SoftDeletableModel
from rest_framework.request import Request

User = get_user_model()
LOGGER = logging.getLogger(__name__)


class DeletionTrackingModel(SoftDeletableModel):
    """Model Helper to track .delete(..) on a model instance
    TODO: Handle bulk_delete, after some-stability prevent soft-delete without user.

    Attributes:
        is_removed (BooleanField): Is the Model Soft Deleted
        removed_by (ForeignKey): User that deleted the instance
    """

    deleted_by_fName = "deleted_by"
    removed_by = models.ForeignKey(
        to=User,
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        default=None,
        related_name="+",
    )

    class Meta:
        abstract = True

    def is_valid_user(self, user: typing.Any) -> bool:
        """Check if this user is valid and not anonymous"""
        return isinstance(user, User) and not isinstance(user, AnonymousUser)

    def _get_user_from_request(self, *args, **kwargs):
        """Fetch user from request"""
        request = kwargs.get("request", None)
        if isinstance(request, (HttpRequest, Request)):
            user = getattr(request, "user", None)
            if self.is_valid_user(user):
                return user

        return None

    def _get_user_from_args_kwargs(self, *args, **kwargs):
        """Get user from args and kwargs"""
        # Check kwargs first
        user = kwargs.get(self.deleted_by_fName, None)
        if self.is_valid_user(user):
            return user

        # Check args
        for arg in args:
            if self.is_valid_user(arg):
                return arg

        return None

    def _get_fallback_user(self):
        """Get a fallback user when no user is found"""
        # Try existing removed_by
        if hasattr(self, "removed_by") and self.removed_by is not None:
            return self.removed_by

        # TODO: Once we build an overriden auth package,
        # It'll have a get_system_user() and we'll use that
        # return User.system_user()
        return None

    def get_user_that_deleted(self, *args, **kwargs):
        """
        Get User that deleted the object
        Priority: request.user > removed_by kwarg > User objects in args > fallback
        """
        # Try request first
        user = self._get_user_from_request(*args, **kwargs)
        if user:
            return user

        # Then try args/kwargs
        user = self._get_user_from_args_kwargs(*args, **kwargs)
        if user:
            return user

        # Finally, fallback
        return self._get_fallback_user()

    def delete(
        self,
        using: typing.Any = None,
        *args: typing.Any,
        soft: bool = True,
        **kwargs: typing.Any,
    ) -> tuple[int, dict[str, int]] | None:
        """
        Soft delete object (set its ``removed_by`` field to Foriegn Reference).
        Actually delete object if setting ``soft`` to False.
        """
        if soft:
            # Prevent overwriting removed_by if already soft-deleted
            if not getattr(self, "is_removed", False):
                user = self.get_user_that_deleted(*args, **kwargs)
                if user:
                    self.removed_by = user
                    self.save(using=using)
                else:
                    LOGGER.warning(
                        f"Could not determine user for deletion of {self.__class__.__name__} pk={self.pk}"
                    )
            else:
                LOGGER.warning(
                    f"Attempted to soft-delete already deleted object {self.__class__.__name__} pk={self.pk}"
                )

        return super().delete(using, *args, soft=soft, **kwargs)
