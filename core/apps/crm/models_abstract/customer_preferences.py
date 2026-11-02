from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from core.apps.crm.constants import PreferenceDataTypeChoices
from core.utils.models import BaseModel


class AbstractCustomerPreferenceType(BaseModel):
    """
    Abstract model defining customer preference types and schemas.
    """

    code = models.CharField(max_length=64, unique=True)
    label = models.CharField(max_length=128)
    data_type = models.CharField(
        max_length=32,
        choices=PreferenceDataTypeChoices.choices,
        default=PreferenceDataTypeChoices.BOOLEAN,
    )
    default_value = models.JSONField(null=True, blank=True, encoder=DjangoJSONEncoder)
    values = models.JSONField(
        default=list,
        blank=True,
        encoder=DjangoJSONEncoder,
        help_text="Allowed choices/options for choice-based preference types.",
    )

    class Meta:
        abstract = True
        verbose_name = "Customer Preference Type"
        verbose_name_plural = "Customer Preference Types"

    def __str__(self):
        return f"{self.label} ({self.code})"

    def clean(self):
        """
        Validate default_value against data_type.

        Ensures that boolean types receive a boolean default, choice types receive
        a value present in the allowed list, and multi-select types receive a subset list.

        Raises:
            ValidationError: If default_value does not conform to the data_type schema.
        """
        if (
            self.data_type == PreferenceDataTypeChoices.BOOLEAN
            and self.default_value is not None
        ):
            if not isinstance(self.default_value, bool):
                raise ValidationError(
                    "default_value must be a boolean for bool data_type."
                )
        elif (
            self.data_type == PreferenceDataTypeChoices.CHOICES
            and self.default_value is not None
        ):
            if self.values and self.default_value not in self.values:
                raise ValidationError(
                    "default_value must be one of the allowed values."
                )
        elif (
            self.data_type == PreferenceDataTypeChoices.MULTI_SELECT
            and self.default_value is not None
        ):
            if not isinstance(self.default_value, list):
                raise ValidationError(
                    "default_value must be a list for multi-select data_type."
                )
            if self.values and not all(v in self.values for v in self.default_value):
                raise ValidationError(
                    "All default_value items must be in allowed values."
                )


class AbstractCustomerPreference(BaseModel):
    """
    Abstract model storing customer preferences.
    """

    customer = models.ForeignKey(
        settings.CRM_CUSTOMER_MODEL,
        on_delete=models.PROTECT,
        related_name="preferences",
    )
    preference_type = models.ForeignKey(
        settings.CRM_CUSTOMER_PREFERENCE_TYPE_MODEL,
        on_delete=models.PROTECT,
        related_name="customer_preferences",
    )
    value = models.JSONField(null=True, blank=True, encoder=DjangoJSONEncoder)

    class Meta:
        abstract = True
        verbose_name = "Customer Preference"
        verbose_name_plural = "Customer Preferences"
        unique_together = [("customer", "preference_type")]

    def __str__(self):
        return f"{self.customer} - {self.preference_type}: {self.value}"

    def clean(self):
        """Validate value against preference_type data_type and allowed values."""
        if not self.preference_type_id:
            return
        pref_type = self.preference_type
        if (
            pref_type.data_type == PreferenceDataTypeChoices.BOOLEAN
            and self.value is not None
        ):
            if not isinstance(self.value, bool):
                raise ValidationError("value must be a boolean.")
        elif (
            pref_type.data_type == PreferenceDataTypeChoices.CHOICES
            and self.value is not None
        ):
            if pref_type.values and self.value not in pref_type.values:
                raise ValidationError(f"value must be one of: {pref_type.values}")
        elif (
            pref_type.data_type == PreferenceDataTypeChoices.MULTI_SELECT
            and self.value is not None
        ):
            if not isinstance(self.value, list):
                raise ValidationError("value must be a list for multi-select.")
            if pref_type.values and not all(v in pref_type.values for v in self.value):
                raise ValidationError(
                    f"All selected items must be in: {pref_type.values}"
                )
