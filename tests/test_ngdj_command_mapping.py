"""Tests for reading the upstream ngdj command mapping."""

from __future__ import annotations

import json
import re
import shutil
import tempfile
import types
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from django_angular3 import ngdj_command_mapping
from django_angular3.changes import ChangeOperation
from django_angular3.ngdj_command_mapping import (
    CommandMapping,
    CommandMappingError,
    NodeCommand,
    installed_openui_schema_version,
    load_command_mapping,
    parse_package_spec,
)
from tests.ngdj_fixture import (
    FIXTURE_DIR,
    fixture_openui_spec_version,
    fixture_package_spec,
    fixture_version,
)
from tests.ngdj_source import NGDJ_PACKAGE_DIR, require_ngdj_source
from tests.workspace_temp import WORKSPACE_TEMP_DIR

# The identities of the staged package come from the fixture, which follows the
# adjacent angular-django2 checkout; nothing here names a release.
PACKAGE_SPEC = fixture_package_spec()
SPEC_VERSION = fixture_openui_spec_version()
_MAJOR, _MINOR = SPEC_VERSION.split(".")[:2]
PATCH_DIFFERENT_SPEC_VERSION = f"{_MAJOR}.{_MINOR}.999"
MINOR_DIFFERENT_SPEC_VERSION = f"{_MAJOR}.{int(_MINOR) + 1}.0"


class CommandMappingTestCase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR)
        self.addCleanup(tmp.cleanup)
        self.workspace = Path(tmp.name)
        package_dir = self.workspace / "node_modules" / "angular-django2"
        (package_dir / "schematics").mkdir(parents=True)
        shutil.copyfile(FIXTURE_DIR / "package.json", package_dir / "package.json")
        for name in ("command-mapping.json", "command-mapping.schema.json"):
            shutil.copyfile(FIXTURE_DIR / name, package_dir / "schematics" / name)
        self.package_dir = package_dir

    def load(self, package_spec: str = PACKAGE_SPEC) -> CommandMapping:
        return load_command_mapping(
            self.workspace,
            package_spec,
            installed_openui_spec_version=SPEC_VERSION,
        )

    def edit_mapping(self, **changes: Any) -> None:
        path = self.package_dir / "schematics" / "command-mapping.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        document.update(changes)
        path.write_text(json.dumps(document), encoding="utf-8")


class ParsePackageSpecTests(unittest.TestCase):
    def test_splits_name_and_optional_version(self) -> None:
        self.assertEqual(
            parse_package_spec("angular-django2@0.7.0"), ("angular-django2", "0.7.0")
        )
        self.assertEqual(
            parse_package_spec("@example/angular-django2@1.2.3"),
            ("@example/angular-django2", "1.2.3"),
        )
        self.assertEqual(
            parse_package_spec("angular-django2"), ("angular-django2", None)
        )
        self.assertEqual(
            parse_package_spec("@example/angular-django2"),
            ("@example/angular-django2", None),
        )


class InstalledOpenUiSchemaVersionTests(unittest.TestCase):
    def stub_package(self, root: Path) -> types.ModuleType:
        package_dir = root / "openui_spec"
        package_dir.mkdir()
        (package_dir / "__init__.py").touch()
        stub = types.ModuleType("openui_spec")
        stub.__file__ = str(package_dir / "__init__.py")
        stub.__version__ = "9.9.9"
        return stub

    def test_reads_schema_version_shipped_as_package_data(self) -> None:
        with tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR) as tmp:
            stub = self.stub_package(Path(tmp))
            (Path(tmp) / "openui_spec" / "SCHEMA_VERSION").write_text(
                "1.2.3\n", encoding="utf-8"
            )

            with patch.object(ngdj_command_mapping, "openui_spec", stub):
                self.assertEqual(installed_openui_schema_version(), "1.2.3")

    def test_reads_schema_version_of_a_source_checkout(self) -> None:
        with tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR) as tmp:
            stub = self.stub_package(Path(tmp))
            (Path(tmp) / "SCHEMA_VERSION").write_text("1.2.3\n", encoding="utf-8")

            with patch.object(ngdj_command_mapping, "openui_spec", stub):
                self.assertEqual(installed_openui_schema_version(), "1.2.3")

    def test_a_package_without_schema_version_names_the_package(self) -> None:
        with tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR) as tmp:
            stub = self.stub_package(Path(tmp))

            with (
                patch.object(ngdj_command_mapping, "openui_spec", stub),
                self.assertRaisesRegex(
                    CommandMappingError, r"openui-spec 9\.9\.9.*SCHEMA_VERSION"
                ),
            ):
                installed_openui_schema_version()


class LoadCommandMappingTests(CommandMappingTestCase):
    def test_loads_the_mapping_of_the_installed_package(self) -> None:
        mapping = self.load()

        self.assertEqual(mapping.mapping_version, 1)
        self.assertEqual(mapping.openui_spec_version, SPEC_VERSION)

    def test_an_unpinned_package_skips_the_version_comparison(self) -> None:
        self.assertEqual(self.load("angular-django2").mapping_version, 1)

    def test_a_scoped_package_is_read_from_its_scope_directory(self) -> None:
        scoped = self.workspace / "node_modules" / "@example"
        scoped.mkdir()
        shutil.move(str(self.package_dir), str(scoped / "angular-django2"))

        mapping = self.load(f"@example/{PACKAGE_SPEC}")

        self.assertEqual(mapping.mapping_version, 1)

    def test_a_missing_package_names_the_path_and_the_package(self) -> None:
        shutil.rmtree(self.package_dir)

        with self.assertRaisesRegex(
            CommandMappingError,
            rf"command-mapping\.json.*{re.escape(PACKAGE_SPEC)}",
        ):
            self.load()

    def test_a_pinned_version_that_differs_from_the_installed_one_names_both(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            CommandMappingError,
            rf"Installed angular-django2 is {re.escape(fixture_version())}"
            r".*pins 0\.0\.1",
        ):
            self.load("angular-django2@0.0.1")

    def test_a_mapping_that_breaks_the_schema_is_rejected(self) -> None:
        path = self.package_dir / "schematics" / "command-mapping.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        del document["ui"]
        path.write_text(json.dumps(document), encoding="utf-8")

        with self.assertRaisesRegex(CommandMappingError, "does not match"):
            self.load()

    def test_an_unsupported_mapping_version_fails_loudly(self) -> None:
        self.edit_mapping(mappingVersion=2)

        with self.assertRaisesRegex(CommandMappingError, "mappingVersion 2"):
            self.load()

    def test_a_different_openui_spec_version_names_both(self) -> None:
        with self.assertRaisesRegex(
            CommandMappingError,
            rf"OpenUI spec {re.escape(SPEC_VERSION)}"
            rf".*installed openui-spec is {re.escape(MINOR_DIFFERENT_SPEC_VERSION)}",
        ):
            load_command_mapping(
                self.workspace,
                PACKAGE_SPEC,
                installed_openui_spec_version=MINOR_DIFFERENT_SPEC_VERSION,
            )

    def test_a_patch_difference_in_the_openui_spec_version_is_accepted(self) -> None:
        mapping = load_command_mapping(
            self.workspace,
            PACKAGE_SPEC,
            installed_openui_spec_version=PATCH_DIFFERENT_SPEC_VERSION,
        )

        self.assertEqual(mapping.openui_spec_version, SPEC_VERSION)

    def test_malformed_json_is_reported_with_its_path(self) -> None:
        path = self.package_dir / "schematics" / "command-mapping.json"
        path.write_text("{", encoding="utf-8")

        with self.assertRaisesRegex(CommandMappingError, "Cannot read .*mapping"):
            self.load()


class CommandMappingAccessorTests(CommandMappingTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.mapping = self.load()

    def test_roles_and_node_types(self) -> None:
        self.assertTrue(self.mapping.has_node_type("Application"))
        self.assertFalse(self.mapping.has_node_type("Hologram"))
        self.assertEqual(self.mapping.role("Application"), "root")
        self.assertEqual(self.mapping.role("Route"), "embedded")
        self.assertIn("DashboardPage", self.mapping.node_types())

    def test_a_root_node_lists_its_commands_with_their_conditions(self) -> None:
        self.assertEqual(
            self.mapping.commands_for("DashboardPage"), (NodeCommand("page", None),)
        )
        surface = self.mapping.commands_for("SurfaceContainers")
        self.assertEqual(
            [command.command for command in surface], ["complex-component", "component"]
        )
        self.assertIn("OverlayContainers", surface[0].when or "")
        self.assertIsNone(surface[1].when)

    def test_an_embedded_node_names_the_root_that_compiles_it(self) -> None:
        self.assertEqual(self.mapping.compiled_by("Route"), ("Application",))
        self.assertEqual(self.mapping.commands_for("Route"), ())

    def test_operation_status_carries_the_reason_and_the_gap(self) -> None:
        update = self.mapping.operation_status("Application", ChangeOperation.UPDATE)
        self.assertEqual(
            (update.status, update.reason, update.gap), ("supported", None, None)
        )

        page_update = self.mapping.operation_status(
            "DashboardPage", ChangeOperation.UPDATE
        )
        self.assertEqual(page_update.status, "unsupported")
        self.assertTrue(page_update.reason)
        self.assertRegex(page_update.gap or "", r"^shlomoa/angular-django2#\d+$")

        indirect = self.mapping.operation_status("Route", ChangeOperation.UPDATE)
        self.assertEqual(
            (indirect.status, indirect.via), ("indirect", ("Application",))
        )

    def test_every_node_type_has_a_status_for_every_operation(self) -> None:
        for node_type in self.mapping.node_types():
            for operation in ChangeOperation:
                with self.subTest(node_type=node_type, operation=operation.value):
                    self.assertTrue(
                        self.mapping.operation_status(node_type, operation).status
                    )

    def test_command_status_and_existing_output_behavior(self) -> None:
        self.assertEqual(
            self.mapping.command_operation_status(
                "data-service", ChangeOperation.CREATE
            ).status,
            "supported",
        )
        self.assertEqual(
            self.mapping.command_operation_status(
                "complex-component", ChangeOperation.UPDATE
            ).status,
            "partial",
        )
        self.assertEqual(self.mapping.on_existing("page"), "refuse-modified")
        self.assertEqual(self.mapping.on_existing("openapi-setup"), "skip")

    def test_unknown_names_are_reported_not_guessed(self) -> None:
        with self.assertRaisesRegex(CommandMappingError, "Unknown OpenUI node type"):
            self.mapping.role("Hologram")
        with self.assertRaisesRegex(CommandMappingError, "Unknown ngdj command"):
            self.mapping.on_existing("hologram")
        with self.assertRaisesRegex(CommandMappingError, "Unknown operation"):
            self.mapping.operation_status("Application", "teleport")


@require_ngdj_source
class FixtureDriftTests(unittest.TestCase):
    """The fixture must equal the adjacent checkout it is synced from.

    Development and integration run against the local ``angular-django2``
    (``ANGULAR_DJANGO2_ROOT`` or the sibling checkout), not a released pin; a
    mismatch means the fixture must be refreshed.
    """

    def test_the_fixture_is_the_version_of_the_adjacent_checkout(self) -> None:
        sibling_version = json.loads(
            (NGDJ_PACKAGE_DIR / "package.json").read_text(encoding="utf-8")
        )["version"]

        self.assertEqual(
            fixture_version(),
            sibling_version,
            "the fixture does not match the adjacent angular-django2; "
            "run tests/fixtures/ngdj/sync_command_mapping.py to refresh it",
        )

    def test_the_fixture_equals_the_sibling_mapping(self) -> None:
        for name in ("command-mapping.json", "command-mapping.schema.json"):
            with self.subTest(file=name):
                self.assertEqual(
                    (FIXTURE_DIR / name).read_bytes(),
                    (NGDJ_PACKAGE_DIR / "schematics" / name).read_bytes(),
                    "fixture drifted; run tests/fixtures/ngdj/sync_command_mapping.py",
                )
