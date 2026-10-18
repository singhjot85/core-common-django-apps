from unittest.mock import MagicMock, patch

import pytest

from core.apps.configurations import get_configuration_model
from core.apps.invoices import get_invoice_template_model
from core.utils.models import (
    BaseSemanaticVersionModel,
    BaseSemanticVersionModel,
    BaseTemplateModel,
)
from core.utils.models.version import (
    InvalidVersionException,
    SemanticVersioningModel,
    SemanticVersionManager,
    SemanticVersionManger,
    validate_version,
)

Configuration = get_configuration_model()
InvoiceTemplate = get_invoice_template_model()


class TestValidateVersion:
    """Unit tests for the validate_version function."""

    @pytest.mark.parametrize(
        "valid_version",
        ["1.0.0", "0.0.1", "2.15.8", "100.200.300"],
    )
    def test_valid_version_strings(self, valid_version):
        """Test that correctly formatted semantic versions pass validation."""
        validate_version(valid_version)

    @pytest.mark.parametrize(
        "invalid_val,expected_error",
        [
            (123, "Invalid Version, expected string"),
            (None, "Invalid Version, expected string"),
            (["1", "0", "0"], "Invalid Version, expected string"),
            ("1.0", "Invalid Version, expected format Major.Minor.Patch"),
            ("1.0.0.0", "Invalid Version, expected format Major.Minor.Patch"),
            ("", "Invalid Version, expected format Major.Minor.Patch"),
            ("x.0.0", "Invalid Version part, Version Major should be a valid int"),
            ("1.y.0", "Invalid Version part, Version Minor should be a valid int"),
            ("1.0.z", "Invalid Version part, Version Patch should be a valid int"),
        ],
    )
    def test_invalid_version_strings(self, invalid_val, expected_error):
        """Test that invalid types, part counts, or non-integer parts raise InvalidVersionException."""
        with pytest.raises(InvalidVersionException) as exc_info:
            validate_version(invalid_val)
        assert expected_error in str(exc_info.value)


class TestSemanticVersioningModelUnits:
    """Unit tests for SemanticVersioningModel logic, clean validation, and field synchronization."""

    def test_default_version_attributes(self):
        """Test model default class attributes."""
        assert SemanticVersioningModel.DEFAULT_VERSION_PARTS == (1, 0, 0)
        assert SemanticVersioningModel.DEFAULT_VERSION == "1.0.0"

    def test_clean_valid_versions(self):
        """Test that clean passes for valid version values."""
        instance = Configuration(version_major=1, version_minor=0, version_patch=0)
        instance.clean()

        instance_higher = Configuration(
            version_major=2, version_minor=5, version_patch=1
        )
        instance_higher.clean()

    def test_clean_skips_when_any_part_is_none(self):
        """Test that clean exits early if any part is None."""
        instance = Configuration(version_major=None, version_minor=0, version_patch=0)
        instance.clean()

    @pytest.mark.parametrize(
        "major,minor,patch,expected_msg",
        [
            (-1, 0, 0, "Version part cannot be negative"),
            (1, -1, 0, "Version part cannot be negative"),
            (1, 0, -1, "Version part cannot be negative"),
            (0, 0, 0, "Version cannot be less than 1.0.0"),
            (-1, 0, 0, "Version part cannot be negative"),
        ],
    )
    def test_clean_raises_for_invalid_parts(self, major, minor, patch, expected_msg):
        """Test that negative parts or versions below 1.0.0 raise InvalidVersionException."""
        instance = Configuration(
            version_major=major, version_minor=minor, version_patch=patch
        )
        with pytest.raises(InvalidVersionException) as exc_info:
            instance.clean()
        assert expected_msg in str(exc_info.value)

    def test_sync_on_adding_state_with_explicit_version(self):
        """Test that newly initialized instances sync parts from version string."""
        instance = Configuration(version="2.4.6")
        instance.resolve_version()
        assert instance.version_major == 2
        assert instance.version_minor == 4
        assert instance.version_patch == 6
        assert instance.version == "2.4.6"

    def test_sync_on_adding_state_with_explicit_parts(self):
        """Test that newly initialized instances sync version string from parts."""
        instance = Configuration(
            version_major=3,
            version_minor=1,
            version_patch=4,
            version=None,
        )
        instance.resolve_version()
        assert instance.version == "3.1.4"
        assert instance.version_major == 3
        assert instance.version_minor == 1
        assert instance.version_patch == 4

    def test_sync_on_existing_instance_when_version_changed(self):
        """Test that existing instance updates parts when version is in dirty fields."""
        instance = Configuration(
            version="1.0.0", version_major=1, version_minor=0, version_patch=0
        )
        instance._state.adding = False
        instance.get_dirty_fields = MagicMock(return_value={"version": "1.0.0"})

        instance.version = "3.2.1"
        instance._sync_version_and_parts()

        assert instance.version_major == 3
        assert instance.version_minor == 2
        assert instance.version_patch == 1

    def test_sync_on_existing_instance_when_parts_changed(self):
        """Test that existing instance updates version string when parts are in dirty fields."""
        instance = Configuration(
            version="1.0.0", version_major=1, version_minor=0, version_patch=0
        )
        instance._state.adding = False
        instance.get_dirty_fields = MagicMock(return_value={"version_major": 1})

        instance.version_major = 2
        instance._sync_version_and_parts()

        assert instance.version == "2.0.0"

    def test_get_version_parts_invalid_format(self):
        """Test that _get_version_parts raises InvalidVersionException for unparseable strings."""
        instance = Configuration(version="invalid_ver")
        with pytest.raises(InvalidVersionException) as exc_info:
            instance._get_version_parts()
        assert "Cannot parse version parts" in str(exc_info.value)

    def test_bump_version_patch(self):
        """Test bumping patch version increments patch and keeps major/minor."""
        instance = Configuration(
            version="1.2.3", version_major=1, version_minor=2, version_patch=3
        )
        instance.save = MagicMock()
        new_version = instance.bump_version(bump_type="patch", commit=False)

        assert new_version == "1.2.4"
        assert instance.version == "1.2.4"
        assert instance.version_major == 1
        assert instance.version_minor == 2
        assert instance.version_patch == 4
        instance.save.assert_not_called()

    def test_bump_version_minor(self):
        """Test bumping minor version increments minor and resets patch to 0."""
        instance = Configuration(
            version="1.2.3", version_major=1, version_minor=2, version_patch=3
        )
        instance.save = MagicMock()
        new_version = instance.bump_version(bump_type="minor", commit=False)

        assert new_version == "1.3.0"
        assert instance.version == "1.3.0"
        assert instance.version_major == 1
        assert instance.version_minor == 3
        assert instance.version_patch == 0
        instance.save.assert_not_called()

    def test_bump_version_major(self):
        """Test bumping major version increments major and resets minor and patch to 0."""
        instance = Configuration(
            version="1.2.3", version_major=1, version_minor=2, version_patch=3
        )
        instance.save = MagicMock()
        new_version = instance.bump_version(bump_type="major", commit=False)

        assert new_version == "2.0.0"
        assert instance.version == "2.0.0"
        assert instance.version_major == 2
        assert instance.version_minor == 0
        assert instance.version_patch == 0
        instance.save.assert_not_called()

    def test_bump_version_invalid_type_raises_value_error(self):
        """Test that an unknown bump_type raises ValueError."""
        instance = Configuration(version="1.0.0")
        with pytest.raises(ValueError) as exc_info:
            instance.bump_version(bump_type="invalid")
        assert "Invalid bump_type" in str(exc_info.value)

    def test_bump_version_commit(self):
        """Test bumping version with commit=True calls save with update_fields."""
        instance = Configuration(
            version="1.0.0", version_major=1, version_minor=0, version_patch=0
        )
        instance._state.adding = False
        instance.save = MagicMock()

        instance.bump_version(bump_type="patch", commit=True)
        instance.save.assert_called_once_with(
            update_fields=["version", "version_major", "version_minor", "version_patch"]
        )


class TestSemanticVersionQuerySetUnits:
    """Unit tests for SemanticVersionQuerySet methods."""

    def test_latest_qs_ordering_extend_bug_fixed(self):
        """Test that passing an ordering list appends correctly and returns a QuerySet."""
        qs = Configuration.objects.all()
        ordered_qs = qs.latest_qs(ordering=["name"])
        assert "name" in ordered_qs.query.order_by

    def test_latest_version_empty_returns_defaults(self):
        """Test that latest_version returns default values when no objects exist."""
        qs = Configuration.objects.none()

        version_str = qs.latest_version(parts=False)
        assert version_str == "1.0.0"

        version_parts = qs.latest_version(parts=True)
        assert version_parts == (1, 0, 0)

    def test_versioned_get_or_create_adds_default_version_and_parts(self):
        """Test that versioned_get_or_create populates version defaults."""
        qs = Configuration.objects.all()
        with patch.object(qs, "get_or_create") as mock_goc:
            mock_goc.return_value = (Configuration(version="1.0.0"), True)
            obj, created = qs.versioned_get_or_create(
                defaults={"name": "test_conf"},
                interface_type="system",
            )
            mock_goc.assert_called_once()
            called_kwargs = mock_goc.call_args[1]
            assert called_kwargs["interface_type"] == "system"
            assert called_kwargs["defaults"]["version"] == "1.0.0"
            assert called_kwargs["defaults"]["version_major"] == 1
            assert called_kwargs["defaults"]["version_minor"] == 0
            assert called_kwargs["defaults"]["version_patch"] == 0
            assert called_kwargs["defaults"]["name"] == "test_conf"

    def test_versioned_update_or_create_created_flow(self):
        """Test versioned_update_or_create when the object is freshly created."""
        qs = Configuration.objects.all()
        created_obj = Configuration(interface_type="app", version="1.0.0")

        mock_locked_qs = MagicMock()
        mock_locked_qs.versioned_get_or_create.return_value = (created_obj, True)

        with patch.object(qs, "select_for_update", return_value=mock_locked_qs):
            with patch("core.utils.models.version.transaction.atomic"):
                obj, created = qs.versioned_update_or_create(
                    interface_type="app",
                    defaults={"details": {"key": "val"}},
                )
                assert created is True
                assert obj == created_obj

    def test_versioned_update_or_create_existing_flow_major_bump(self):
        """Test versioned_update_or_create increments major version and resets subordinate parts."""
        qs = Configuration.objects.all()
        existing_obj = Configuration(
            interface_type="app",
            version="1.2.3",
            version_major=1,
            version_minor=2,
            version_patch=3,
        )
        existing_obj.save = MagicMock()

        mock_locked_qs = MagicMock()
        mock_locked_qs.versioned_get_or_create.return_value = (existing_obj, False)

        with patch.object(qs, "select_for_update", return_value=mock_locked_qs):
            with patch("core.utils.models.version.transaction.atomic"):
                obj, created = qs.versioned_update_or_create(
                    defaults={"name": "New Name"},
                    bump_type="major",
                    interface_type="app",
                )
                assert created is False
                assert obj.version == "2.0.0"
                assert obj.version_major == 2
                assert obj.version_minor == 0
                assert obj.version_patch == 0
                assert obj.name == "New Name"
                existing_obj.save.assert_called_once()

    def test_versioned_update_or_create_existing_flow_minor_bump(self):
        """Test versioned_update_or_create increments minor version and resets patch."""
        qs = Configuration.objects.all()
        existing_obj = Configuration(
            interface_type="app",
            version="1.2.3",
            version_major=1,
            version_minor=2,
            version_patch=3,
        )
        existing_obj.save = MagicMock()

        mock_locked_qs = MagicMock()
        mock_locked_qs.versioned_get_or_create.return_value = (existing_obj, False)

        with patch.object(qs, "select_for_update", return_value=mock_locked_qs):
            with patch("core.utils.models.version.transaction.atomic"):
                obj, created = qs.versioned_update_or_create(
                    filters={"interface_type": "app"},
                    defaults={"name": "Minor Bump"},
                    bump_type="minor",
                )
                assert created is False
                assert obj.version == "1.3.0"
                assert obj.version_major == 1
                assert obj.version_minor == 3
                assert obj.version_patch == 0

    def test_versioned_update_or_create_existing_flow_patch_bump(self):
        """Test versioned_update_or_create increments patch version only."""
        qs = Configuration.objects.all()
        existing_obj = Configuration(
            interface_type="app",
            version="1.2.3",
            version_major=1,
            version_minor=2,
            version_patch=3,
        )
        existing_obj.save = MagicMock()

        mock_locked_qs = MagicMock()
        mock_locked_qs.versioned_get_or_create.return_value = (existing_obj, False)

        with patch.object(qs, "select_for_update", return_value=mock_locked_qs):
            with patch("core.utils.models.version.transaction.atomic"):
                obj, created = qs.versioned_update_or_create(
                    interface_type="app",
                    defaults={"name": "Patch Bump"},
                    bump_type="patch",
                )
                assert created is False
                assert obj.version == "1.2.4"
                assert obj.version_major == 1
                assert obj.version_minor == 2
                assert obj.version_patch == 4

    def test_versioned_update_or_create_invalid_bump_type(self):
        """Test that invalid bump_type in versioned_update_or_create raises ValueError."""
        qs = Configuration.objects.all()
        existing_obj = Configuration(
            interface_type="app",
            version="1.0.0",
            version_major=1,
            version_minor=0,
            version_patch=0,
        )

        mock_locked_qs = MagicMock()
        mock_locked_qs.versioned_get_or_create.return_value = (existing_obj, False)

        with patch.object(qs, "select_for_update", return_value=mock_locked_qs):
            with patch("core.utils.models.version.transaction.atomic"):
                with pytest.raises(ValueError) as exc_info:
                    qs.versioned_update_or_create(
                        interface_type="app",
                        bump_type="unsupported",
                    )
                assert "Invalid bump_type" in str(exc_info.value)

    def test_manager_alias_backward_compatibility(self):
        """Test that SemanticVersionManger alias is preserved."""
        assert SemanticVersionManger is SemanticVersionManager


class TestBaseSemanticVersionModel:
    """Unit tests for BaseSemanticVersionModel abstract class and constants."""

    def test_meta_abstract(self):
        """Ensure BaseSemanticVersionModel is marked abstract."""
        assert BaseSemanticVersionModel._meta.abstract is True

    def test_backward_compatibility_alias(self):
        """Ensure BaseSemanaticVersionModel alias points to BaseSemanticVersionModel."""
        assert BaseSemanaticVersionModel is BaseSemanticVersionModel

    def test_bump_types_constant(self):
        """Ensure bump types tuple is correctly declared."""
        assert BaseSemanticVersionModel._bump_types == ("major", "minor", "patch")


class TestBaseTemplateModel:
    """Unit tests for BaseTemplateModel rendering helpers."""

    def test_meta_abstract(self):
        """Ensure BaseTemplateModel is marked abstract."""
        assert BaseTemplateModel._meta.abstract is True

    def test_render_using_django_engine(self):
        """Test rendering plain and HTML template content using Django engine."""
        template = InvoiceTemplate(
            html_content="<h1>Hello {{ name }}</h1>",
            plain_content="Hello {{ name }}",
        )
        html_out, text_out = template.render_using_django_engine({"name": "Alice"})
        assert html_out == "<h1>Hello Alice</h1>"
        assert text_out == "Hello Alice"

    def test_render_using_django_engine_partial_content(self):
        """Test rendering when one of the template fields is empty or None."""
        template = InvoiceTemplate(
            html_content=None,
            plain_content="Text only for {{ user }}",
        )
        html_out, text_out = template.render_using_django_engine({"user": "Bob"})
        assert html_out is None
        assert text_out == "Text only for Bob"

    def test_render_template_context_merging_and_defaults(self):
        """Test that render_template merges template_mapping with dynamic rendering_context."""
        template = InvoiceTemplate(
            html_content="<p>{{ app_name }}: {{ user_msg }}</p>",
            plain_content="{{ app_name }}: {{ user_msg }}",
            template_mapping={"app_name": "CoreApp", "user_msg": "Default"},
        )
        html_out, text_out = template.render_template({"user_msg": "Custom Message"})
        assert html_out == "<p>CoreApp: Custom Message</p>"
        assert text_out == "CoreApp: Custom Message"

    def test_render_template_with_none_mapping_and_none_context(self):
        """Test that render_template handles None template_mapping and None rendering_context gracefully."""
        template = InvoiceTemplate(
            html_content="Static HTML",
            plain_content="Static Plain",
            template_mapping=None,
        )
        html_out, text_out = template.render_template(None)
        assert html_out == "Static HTML"
        assert text_out == "Static Plain"

    def test_render_template_engine_django_case_insensitive(self):
        """Test that specifying 'Django' or 'DJANGO' as engine works properly."""
        template = InvoiceTemplate(
            html_content="<b>{{ title }}</b>",
            template_mapping={"title": "Test"},
        )
        html_out, _ = template.render_template(engine="DJANGO")
        assert html_out == "<b>Test</b>"

    def test_render_template_unsupported_engine_raises_not_implemented(self):
        """Test that requesting an unsupported engine raises NotImplementedError."""
        template = InvoiceTemplate(html_content="Hello")
        with pytest.raises(NotImplementedError) as exc_info:
            template.render_template(engine="jinja2")
        assert "Template engine 'jinja2' is not supported" in str(exc_info.value)
