"""
Unit tests for core.libraries.seeder components.
"""

from __future__ import annotations

import json

import pytest
from django.db import models

from core.libraries.seeder.exceptions import (
    FieldException,
    InvalidFieldError,
    SeederDataLoaderException,
    SeederException,
)
from core.libraries.seeder.fields import (
    ForwardSingularRelation,
    RelationField,
    SeederField,
)
from core.libraries.seeder.loaders.static import FileBasedLoader
from core.libraries.seeder.methods.base import BaseObjectMethods
from core.libraries.seeder.methods.defaults import (
    CreateObject,
    GetorCreateObject,
)
from core.libraries.seeder.registry import fixture_registry, seeder_registry
from core.libraries.seeder.seeder import BaseSeeder


# ---------------------------------------------------------------------------
# Dummy Models for Unit Testing
# ---------------------------------------------------------------------------
class DummyParentModel(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=20, default="DEFAULT")
    notes = models.TextField(null=True, blank=True)

    class Meta:
        app_label = "test_libraries_seeder"

    def __str__(self) -> str:
        return self.name


class DummyChildModel(models.Model):
    parent = models.ForeignKey(
        DummyParentModel, related_name="children", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=50)

    class Meta:
        app_label = "test_libraries_seeder"

    def __str__(self) -> str:
        return self.title


# ---------------------------------------------------------------------------
# Tests for Exceptions
# ---------------------------------------------------------------------------
class TestSeederExceptions:
    """Validate exception message formatting and standard inheritance."""

    def test_seeder_exception_with_label(self):
        exc = SeederException(label="CustomSeeder", message="Something broke")
        assert str(exc) == "[CustomSeeder] Something broke"

    def test_seeder_exception_without_label(self):
        exc = SeederException(message="Generic failure")
        assert str(exc) == "Generic failure"

    def test_seeder_data_loader_exception(self):
        exc = SeederDataLoaderException("file_loader", "File not found")
        assert "Exception loading data from file_loader: File not found" in str(exc)

    def test_invalid_field_error(self):
        exc = InvalidFieldError("invalid_col", DummyParentModel)
        assert "'invalid_col' is an invalid field for model: DummyParentModel" in str(
            exc
        )

    def test_field_exception(self):
        exc = FieldException("code", DummyParentModel, "Value too long")
        assert (
            "Error in field 'code' of model 'DummyParentModel': Value too long"
            in str(exc)
        )


# ---------------------------------------------------------------------------
# Tests for Seeder Fields & Relations
# ---------------------------------------------------------------------------
class TestSeederFields:
    """Validate field and relationship descriptors."""

    def test_seeder_field_is_required(self):
        # name has no default and not null -> required
        req_field = SeederField("name", DummyParentModel, "Alpha")
        assert req_field.is_required is True

        # code has default -> not required
        def_field = SeederField("code", DummyParentModel, "C1")
        assert def_field.is_required is False

        # notes is null=True -> not required
        opt_field = SeederField("notes", DummyParentModel, "Some notes")
        assert opt_field.is_required is False

    def test_seeder_field_get_value_with_hook(self):
        field = SeederField("name", DummyParentModel, "alpha")

        class SampleSeeder:
            def get_name(self, raw_value):
                return raw_value.upper()

        val = field.get_value(SampleSeeder())
        assert val == "ALPHA"

    def test_seeder_field_get_value_without_hook(self):
        field = SeederField("name", DummyParentModel, "alpha")

        class SimpleSeeder:
            pass

        assert field.get_value(SimpleSeeder()) == "alpha"

    def test_forward_singular_relation_is_required(self):
        # parent foreign key on DummyChildModel is null=False -> required
        fwd_rel = ForwardSingularRelation({}, "parent", DummyChildModel, "parent_val")
        assert fwd_rel.is_required is True

    def test_relation_field_retrieve_related_instance_malformed(self):
        rel_field_non_dict = RelationField({}, "parent", DummyChildModel, "not-a-dict")
        with pytest.raises(FieldException) as exc_info:
            rel_field_non_dict.retrieve_related_instance()
        assert "expected dictionary containing '$ref' key" in str(exc_info.value)

        rel_field_bad_ref = RelationField(
            {}, "parent", DummyChildModel, {"$ref": "not-a-dict"}
        )
        with pytest.raises(FieldException) as exc_info2:
            rel_field_bad_ref.retrieve_related_instance()
        assert "Malformed $ref payload" in str(exc_info2.value)


# ---------------------------------------------------------------------------
# Tests for File-Based Loaders
# ---------------------------------------------------------------------------
class TestFileBasedLoader:
    """Validate FileBasedLoader discovery and parsing."""

    def test_get_data_with_single_compiled_file(self, tmp_path):
        data_file = tmp_path / "records.json"
        data_file.write_text(json.dumps([{"name": "Item 1"}, {"name": "Item 2"}]))

        loader = FileBasedLoader(directory_name=str(data_file))
        records = loader.get_data()

        assert len(records) == 2
        assert records[0]["name"] == "Item 1"
        assert records[1]["name"] == "Item 2"

    def test_get_data_with_directory_individual(self, tmp_path):
        f1 = tmp_path / "item1.json"
        f1.write_text(json.dumps({"name": "Item 1"}))
        f2 = tmp_path / "item2.json"
        f2.write_text(json.dumps({"name": "Item 2"}))

        loader = FileBasedLoader(
            directory_name=str(tmp_path),
            load_method=FileBasedLoader.LOAD_INDIVIDUAL,
        )
        records = loader.get_data()

        assert len(records) == 2
        names = {r["name"] for r in records}
        assert names == {"Item 1", "Item 2"}

    def test_get_data_missing_path_returns_empty_list(self):
        loader = FileBasedLoader(directory_name="non_existent_directory_12345")
        assert loader.get_data() == []

    def test_get_data_aggregates_from_both_setup_and_core_setup(
        self, tmp_path, settings
    ):
        host_setup = tmp_path / "host_setup"
        host_setup.mkdir()
        (host_setup / "data.json").write_text(json.dumps([{"name": "Host Record"}]))

        core_setup = tmp_path / "core_setup"
        core_setup.mkdir()
        (core_setup / "data.json").write_text(json.dumps([{"name": "Core Record"}]))

        settings.SETUP_DIR = str(tmp_path / "host_setup")
        settings.CORE_SETUP_DIR = str(tmp_path / "core_setup")

        loader = FileBasedLoader(directory_name="data.json")
        records = loader.get_data()

        names = [r["name"] for r in records]
        assert "Host Record" in names
        assert "Core Record" in names


# ---------------------------------------------------------------------------
# Tests for Persistence Methods
# ---------------------------------------------------------------------------
class TestPersistenceMethods:
    """Validate method strategies (GetorCreateObject, CreateObject, etc.)."""

    def test_get_or_create_split_fields(self):
        strategy = GetorCreateObject(
            model=DummyParentModel,
            lookup_fields=["name"],
            default_fields=["code", "notes"],
        )

        prepared = [
            SeederField("name", DummyParentModel, "TestName"),
            SeederField("code", DummyParentModel, "TEST"),
            SeederField("notes", DummyParentModel, "Note A"),
        ]

        class PlainSeeder:
            pass

        dummy_seeder = PlainSeeder()
        lookups, defaults, related = strategy.split_fields(prepared, dummy_seeder)

        assert lookups == {"name": "TestName"}
        assert defaults == {"code": "TEST", "notes": "Note A"}
        assert related == []

    def test_create_object_initialization(self):
        strategy = CreateObject(
            model=DummyParentModel,
            fields=["name", "code"],
        )
        assert strategy.fields == ["name", "code"]
        assert strategy.seed_method == "create"

    def test_prepare_fields_filters_undeclared_fields(self):
        strategy = BaseObjectMethods(
            model=DummyParentModel,
            fields=["name"],
        )
        payload = {"name": "Test", "undeclared_key": "Ignored"}
        prepared = strategy.prepare_fields(payload)

        assert len(prepared) == 1
        assert prepared[0].field_name == "name"


# ---------------------------------------------------------------------------
# Tests for BaseSeeder Subclasses & Registry
# ---------------------------------------------------------------------------
class TestBaseSeederSubclasses:
    """Validate BaseSeeder subclass registration and lifecycle."""

    def test_subclass_registered_in_seeder_registry(self):
        class UniqueTestSeeder(BaseSeeder):
            label = "unique_test_seeder"

        assert seeder_registry.get("unique_test_seeder") is UniqueTestSeeder

    def test_fixture_subclass_registered_in_fixture_registry(self):
        class UniqueFixtureSeeder(BaseSeeder):
            label = "unique_fixture_seeder"
            is_fixture = True

        assert fixture_registry.get("unique_fixture_seeder") is UniqueFixtureSeeder
        assert seeder_registry.get("unique_fixture_seeder") is UniqueFixtureSeeder

    def test_seeder_label_defaults_to_snake_case(self):
        class AutoLabeledSampleSeeder(BaseSeeder):
            pass

        instance = AutoLabeledSampleSeeder()
        assert instance.seeder_label == "auto_labeled_sample_seeder"

    def test_run_without_method_raises(self):
        class IncompleteSeeder(BaseSeeder):
            pass

        seeder = IncompleteSeeder()
        with pytest.raises(SeederException) as exc_info:
            seeder.run(data=[{"name": "X"}])
        assert "No persistence method configured" in str(exc_info.value)
