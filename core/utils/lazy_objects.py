import enum

from django.db.models import TextChoices
from django.utils.functional import LazyObject


class DynamicChoiceType:
    """
    A base class to represent a dynamic set of choices.

    Each attribute should represent a choice tuple (value, label)
    choices returns a list of all such choices.
    """

    @property
    def choices(self):
        """
        Return list of all choices values stored in objecsts dict

        Returns:
            list
        """

        return [value for _, value in self.__dict__.items()]

    @property
    def values(self):
        """
        Return the raw value for all choices stored in object.

        Returns:
            list
        """
        return [value[0] for _, value in self.__dict__.items()]


class TupleEnum(tuple, enum.ReprEnum):

    @property
    def value(self):
        return self[0]

    @property
    def label(self):
        return self[1]

    def __str__(self):
        return self.value


class LazyDynamicChoiceTypes(LazyObject):

    def _setup(self):
        self._wrapped = DynamicChoiceType()

    def __getattr__(self, name):
        value = super().__getattr__(name)

        if value and isinstance(value, (tuple, list)):
            return value[0]

        return value

    def contribute(self, choices: dict | enum.EnumType, **kwargs):
        if isinstance(choices, dict):
            for key, val in choices.items():
                setattr(self, key, (key, val))

        elif isinstance(choices, enum.EnumType):
            for member_name, member in choices.__members__.items():
                if isinstance(member, TupleEnum):
                    setattr(self, member_name, member)
                elif isinstance(member.value, tuple):
                    setattr(self, member_name, member.value)
                elif isinstance(member, TextChoices):
                    setattr(self, member_name, (member.value, member.label))
                else:
                    setattr(self, member_name, (member_name, member.value))
        else:
            raise ValueError("choices must be dict or enum")

    @property
    def choices(self):
        self._wrapped.choices

    @property
    def values(self):
        self._wrapped.values
