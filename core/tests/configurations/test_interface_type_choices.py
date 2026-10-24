"""
Unit tests for dynamic interface_type choices on Configuration and ConfigurationSchema models.
"""

import pytest
from django.core.exceptions import ValidationError

from core.apps.configurations import (
    get_configuration_model,
    get_configuration_schema_model,
)
from core.apps.configurations.constants import (
    get_interface_type_choices,
)

Configuration = get_configuration_model()
ConfigurationSchema = get_configuration_schema_model()


class TestInterfaceTypeChoices:
    """
    Test suite for dynamic evaluation of interface_type choices.
    """

    def test_get_interface_type_choices_returns_callable_choices(self):
        """
        Ensure get_interface_type_choices is callable and returns current choices.
        """
        assert callable(get_interface_type_choices)
        choices = get_interface_type_choices()
        assert isinstance(choices, list)
        assert ("ui_configuration", "UI Configuration") in choices
        assert ("users_template_label", "Users Template Label") in choices

    def test_configuration_model_field_validates_valid_choice(self):
        """
        Verify that field.clean() succeeds for dynamically registered choices.
        """
        field = Configuration._meta.get_field("interface_type")

        # Both default choices should pass clean()
        cleaned_ui = field.clean("ui_configuration", None)
        assert cleaned_ui == "ui_configuration"

        cleaned_label = field.clean("users_template_label", None)
        assert cleaned_label == "users_template_label"

    def test_configuration_model_field_rejects_invalid_choice(self):
        """
        Verify that field.clean() raises ValidationError for unknown choices.
        """
        field = Configuration._meta.get_field("interface_type")

        with pytest.raises(ValidationError) as exc_info:
            field.clean("non_existent_interface_type", None)

        assert "Value 'non_existent_interface_type' is not a valid choice." in str(
            exc_info.value
        )

    def test_configuration_schema_model_field_validates_valid_choice(self):
        """
        Verify that ConfigurationSchema.interface_type validates choices dynamically.
        """
        field = ConfigurationSchema._meta.get_field("interface_type")

        cleaned = field.clean("ui_configuration", None)
        assert cleaned == "ui_configuration"

        with pytest.raises(ValidationError):
            field.clean("invalid_choice_value", None)
