from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

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

    def link_relation(self, instance):
        setattr(instance, self.fk_field_name, self.related_instance)
        instance.save(update_fields=[self.fk_field_name])


@dataclass
class ReverseSingularRelation(BaseModelRelation):
    """
    Reverse ``OneToOne`` set FK on the *related* instance and save it.
    Only special handling that is different from all.
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
