from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    from django.db.models import Model


@dataclass
class BaseModelRelation:
    """Base class for deferred relation linking."""

    related_instance: "Model"  # Instance retrieved/created for the realted reference

    def link_relation(self, instance: "Model") -> None:
        """
        Attach the related instance to `instance` via the accessor.
        Override in subclasses if the accessor semantics differ.
        """
        raise NotImplementedError


@dataclass
class ForwardSingularRelation(BaseModelRelation):
    """
    Forward ``ForeignKey`` and ``OneToOne``
    Set the field on current`instance` and save the current instance.
    """

    fk_field_name: str

    @property
    def is_required(self) -> bool:
        """
        Is this related model required for object creation.
        """
        field = self.related_instance._meta.get_field(self.fk_field_name)

        if field.null or field.has_default():
            return False

        if self._constraint_requires_field(self.related_instance, self.fk_field_name):
            return True

        return not field.blank

    def _constraint_requires_field(model: models.Model, field_name: str) -> bool:
        """
        Return True if any UniqueConstraint/Index includes field_name.

        Args:
            model: class or object of the model.
            field_name (str): Attribute name of the field.

        Returns:
            True if the field in model constraints.
        """
        for constraint in model._meta.constraints:
            if isinstance(constraint, (models.UniqueConstraint, models.Index)):
                if field_name in constraint.fields:
                    return True

        for index in model._meta.indexes:
            if field_name in index.fields:
                return True

        return False

    def link_relation(self, instance):
        """
        Link the related object to the instance.
        """
        setattr(instance, self.fk_field_name, self.related_instance)
        instance.save(update_fields=[self.fk_field_name])


@dataclass
class ReverseSingularRelation(BaseModelRelation):
    """
    Reverse ``OneToOne`` set FK on the *related* instance and save it.
    Only special handling that is different from all.

    TODO: allow_null here needs better handling, we might need to delay creation
    of related_instance (till we have instance) for this to work
    """

    fk_field_name: str

    def link_relation(self, instance):
        setattr(self.related_instance, self.fk_field_name, instance)
        self.related_instance.save(update_fields=[self.fk_field_name])


@dataclass
class ManagerRelation(BaseModelRelation):
    """
    Forward ``ManyToMany``, reverse ``ForeignKey``and reverse ``ManyToMany``
    All these fetch a RelatedManager using the accessor and a ``.add()``
    """

    accessor_name: str  # field name (forward) or get_accessor_name() (reverse)

    def link_relation(self, instance):
        RelatedManager = getattr(instance, self.accessor_name)
        RelatedManager.add(self.related_instance)
