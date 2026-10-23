"""
Unit tests for centralized UI labels, database-backed configurations, and seeders.
"""

from unittest.mock import MagicMock, patch

from django.test import RequestFactory, override_settings

from core.apps.configurations import get_configuration_model
from core.apps.configurations.fixtures.seeders import UsersTemplateLabelFixtureSeeder
from core.apps.users.api.template_views import LoginView
from core.seeder.registry import fixture_registry, seeder_registry
from core.setup.users.seeders import DevUsersTemplateLabelSeeder
from core.utils.labels import (
    LabelDict,
    extract_label_for_language,
    get_current_ui_language,
    get_db_template_labels,
    get_default_labels,
    resolve_labels,
)

Configuration = get_configuration_model()


class TestLabelsAndLabelDict:
    """Test suite for LabelDict proxy and label resolution."""

    def test_default_labels_contain_core_keys(self):
        labels = get_default_labels()
        assert labels.email == "Email"
        assert labels["email"] == "Email"
        assert labels.password == "Password"  # pragma: allowlist secret
        assert labels["password"] == "Password"  # pragma: allowlist secret
        assert labels.sign_in == "Sign In"
        assert labels.create_account == "Create Account"

    def test_backend_override_priority(self):
        backend_labels = {
            "email": "Company Email",
            "sign_in": "Log In Now",
        }
        labels = resolve_labels(backend_labels)

        # Overridden keys return backend values
        assert labels.email == "Company Email"
        assert labels["email"] == "Company Email"
        assert labels.sign_in == "Log In Now"

        # Non-overridden keys fall back to humanized default
        assert labels.password == "Password"  # pragma: allowlist secret
        assert labels["password"] == "Password"  # pragma: allowlist secret
        assert labels.create_account == "Create Account"

    def test_unregistered_key_humanized_fallback(self):
        labels = resolve_labels()
        assert labels.billing_zip_code == "Billing Zip Code"
        assert labels["shipping_address"] == "Shipping Address"
        assert labels.get("vat_number") == "Vat Number"

    def test_none_values_in_backend_dict_do_not_override_defaults(self):
        labels = resolve_labels(
            {"email": None, "password": "Custom Password"}  # pragma: allowlist secret
        )
        assert labels.email == "Email"
        assert labels.password == "Custom Password"  # pragma: allowlist secret

    def test_resolve_labels_idempotent(self):
        initial = LabelDict({"email": "Test Email"})
        resolved = resolve_labels(initial)
        assert resolved is initial
        assert resolved.email == "Test Email"

    def test_base_template_view_injects_labels(self):
        factory = RequestFactory()
        request = factory.get("/login/")
        view = LoginView()
        view.setup(request)
        context = view.get_context_data()

        assert "labels" in context
        labels = context["labels"]
        assert isinstance(labels, LabelDict)
        assert labels.email == "Email"
        assert labels.password == "Password"  # pragma: allowlist secret

    def test_base_template_view_respects_custom_view_labels(self):
        class CustomLoginView(LoginView):
            labels = {"email": "Work Email"}

        factory = RequestFactory()

        request = factory.get("/login/")
        view = CustomLoginView()
        view.setup(request)
        context = view.get_context_data()

        labels = context["labels"]
        assert labels.email == "Work Email"
        assert labels.password == "Password"  # pragma: allowlist secret


class TestDatabaseLabelConfigurationAndLanguageMapping:
    """Tests for multi-language extraction, DB resolution, and fallback."""

    def test_extract_label_for_language(self):
        mapping = {"en": "Sign In", "es": "Iniciar sesión", "fr": "Se connecter"}
        assert extract_label_for_language(mapping, "es") == "Iniciar sesión"
        assert extract_label_for_language(mapping, "fr") == "Se connecter"
        assert extract_label_for_language(mapping, "en") == "Sign In"
        # Only 'en' fallback when requested language is missing
        assert extract_label_for_language(mapping, "de") == "Sign In"
        # Plain string passes through
        assert extract_label_for_language("Simple String", "es") == "Simple String"

    @override_settings(LANGUAGE_CODE="es")
    def test_get_current_ui_language_respects_settings(self):
        assert get_current_ui_language() == "es"

    def test_get_db_template_labels_extracts_mapped_language(self):
        mock_db_details = {
            "sign_in": {"en": "Sign In (DB)", "es": "Iniciar sesión (DB)"},
            "email": {"en": "Email (DB)", "es": "Correo (DB)"},
        }

        with patch.object(
            Configuration, "get_configuration", return_value=mock_db_details
        ):
            labels_es = get_db_template_labels("users_template_label", language="es")
            assert labels_es["sign_in"] == "Iniciar sesión (DB)"
            assert labels_es["email"] == "Correo (DB)"

            labels_en = get_db_template_labels("users_template_label", language="en")
            assert labels_en["sign_in"] == "Sign In (DB)"
            assert labels_en["email"] == "Email (DB)"

    def test_get_db_template_labels_falls_back_on_exception(self):
        with patch.object(
            Configuration, "get_configuration", side_effect=Exception("DB Down")
        ):
            labels = get_db_template_labels("users_template_label")
            assert labels == {}

    def test_resolve_labels_layers_db_over_humanized_fallback(self):
        mock_db_details = {
            "sign_in": {"en": "DB Sign In"},
        }
        with patch.object(
            Configuration, "get_configuration", return_value=mock_db_details
        ):
            resolved = resolve_labels(
                interface_type="users_template_label", language="en"
            )
            # Overridden by DB
            assert resolved.sign_in == "DB Sign In"
            # Non-overridden falls back to humanized default
            assert resolved.password == "Password"  # pragma: allowlist secret

    def test_resolve_labels_backend_overrides_db_and_humanized(self):
        mock_db_details = {
            "sign_in": {"en": "DB Sign In"},
            "email": {"en": "DB Email"},
        }
        with patch.object(
            Configuration, "get_configuration", return_value=mock_db_details
        ):
            resolved = resolve_labels(
                backend_labels={"sign_in": "Backend Top Priority"},
                interface_type="users_template_label",
                language="en",
            )
            # Backend priority overrides DB
            assert resolved.sign_in == "Backend Top Priority"
            # DB overrides humanized fallback
            assert resolved.email == "DB Email"
            # Humanized default retained for untouched keys
            assert resolved.password == "Password"  # pragma: allowlist secret


class TestUsersTemplateLabelSeeders:
    """Tests for UsersTemplateLabelFixtureSeeder and DevUsersTemplateLabelSeeder."""

    def test_seeder_registry_memberships(self):
        assert (
            fixture_registry.get("users_template_label_fixture_seeder")
            is UsersTemplateLabelFixtureSeeder
        )
        assert (
            seeder_registry.get("dev_users_template_label_seeder")
            is DevUsersTemplateLabelSeeder
        )

    def test_fixture_seeder_meta_properties(self):
        assert UsersTemplateLabelFixtureSeeder.Meta.is_fixture is True
        assert UsersTemplateLabelFixtureSeeder.Meta.model == Configuration
        assert (
            UsersTemplateLabelFixtureSeeder.Meta.data_source.load_method == "individual"
        )
        assert (
            "configurations/fixtures/configuration"
            in UsersTemplateLabelFixtureSeeder.Meta.data_source.file_path
        )

    def test_dev_seeder_inherits_with_fixture_false(self):
        assert DevUsersTemplateLabelSeeder.Meta.is_fixture is False
        assert DevUsersTemplateLabelSeeder.Meta.model == Configuration

    def test_seeder_create_uses_set_config_without_cache(self):
        seeder = UsersTemplateLabelFixtureSeeder()
        sample_data = {
            "name": "Users Template Labels",
            "interface_type": "users_template_label",
            "details": {"sign_in": {"en": "Sign In"}},
        }

        with patch.object(
            Configuration, "set_config", return_value=MagicMock()
        ) as mock_set:
            seeder.create(sample_data)
            mock_set.assert_called_once_with(
                interface_type="users_template_label",
                details={"sign_in": {"en": "Sign In"}},
                name="Users Template Labels",
                set_cache=False,
            )

    def test_fixture_file_contents_valid_json(self):
        seeder = UsersTemplateLabelFixtureSeeder()
        data = seeder.seed_data
        assert isinstance(data, list)
        assert len(data) >= 1
        items = [d for d in data if d.get("interface_type") == "users_template_label"]
        assert len(items) == 1
        item = items[0]
        assert item["interface_type"] == "users_template_label"
        assert "sign_in" in item["details"]
        assert item["details"]["sign_in"]["en"] == "Sign In"
        assert item["details"]["sign_in"]["es"] == "Iniciar sesión"
