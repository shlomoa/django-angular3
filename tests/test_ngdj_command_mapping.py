"""Tests for reading the upstream ngdj command mapping."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any

from django_angular3.changes import ChangeOperation
from django_angular3.ngdj_command_mapping import (
    CommandMapping,
    CommandMappingError,
    NodeCommand,
    load_command_mapping,
    parse_package_spec,
)
from tests.workspace_temp import WORKSPACE_TEMP_DIR

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "ngdj"
SIBLING_PACKAGE_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "angular-django2"
    / "projects"
    / "angular-django2"
)
PACKAGE_SPEC = "angular-django2@0.7.0"
SPEC_VERSION = "0.12.1"


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

        mapping = self.load("@example/angular-django2@0.7.0")

        self.assertEqual(mapping.mapping_version, 1)

    def test_a_missing_package_names_the_path_and_the_package(self) -> None:
        shutil.rmtree(self.package_dir)

        with self.assertRaisesRegex(
            CommandMappingError, r"command-mapping\.json.*angular-django2@0\.7\.0"
        ):
            self.load()

    def test_a_pinned_version_that_differs_from_the_installed_one_names_both(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            CommandMappingError, r"Installed angular-django2 is 0\.7\.0.*pins 0\.6\.1"
        ):
            self.load("angular-django2@0.6.1")

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
            r"OpenUI spec 0\.12\.1.*installed openui-spec is 0\.13\.0",
        ):
            load_command_mapping(
                self.workspace,
                PACKAGE_SPEC,
                installed_openui_spec_version="0.13.0",
            )

    def test_a_patch_difference_in_the_openui_spec_version_is_accepted(self) -> None:
        mapping = load_command_mapping(
            self.workspace, PACKAGE_SPEC, installed_openui_spec_version="0.12.0"
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


class FixtureVersionTests(unittest.TestCase):
    def test_the_fixture_is_the_version_the_shipped_configuration_pins(self) -> None:
        shipped = json.loads(
            (
                Path(__file__).resolve().parent.parent
                / "django_angular3"
                / "django-angular3.json"
            ).read_text(encoding="utf-8")
        )["tool"]["ngAddPackage"]
        fixture = json.loads((FIXTURE_DIR / "package.json").read_text(encoding="utf-8"))

        self.assertEqual(
            (fixture["name"], fixture["version"]),
            parse_package_spec(shipped),
            "tool.ngAddPackage changed; regenerate the fixture with "
            "tests/fixtures/ngdj/sync_command_mapping.py",
        )


@unittest.skipUnless(
    SIBLING_PACKAGE_DIR.is_dir(), "angular-django2 sibling repository is required"
)
class FixtureDriftTests(unittest.TestCase):
    def test_the_fixture_equals_the_sibling_mapping_of_the_same_version(self) -> None:
        fixture_version = json.loads(
            (FIXTURE_DIR / "package.json").read_text(encoding="utf-8")
        )["version"]
        sibling_version = json.loads(
            (SIBLING_PACKAGE_DIR / "package.json").read_text(encoding="utf-8")
        )["version"]
        if sibling_version != fixture_version:
            self.skipTest(
                f"sibling is {sibling_version}, fixture is {fixture_version}; "
                "run tests/fixtures/ngdj/sync_command_mapping.py to refresh it"
            )

        for name in ("command-mapping.json", "command-mapping.schema.json"):
            with self.subTest(file=name):
                self.assertEqual(
                    (FIXTURE_DIR / name).read_bytes(),
                    (SIBLING_PACKAGE_DIR / "schematics" / name).read_bytes(),
                    "fixture drifted; run tests/fixtures/ngdj/sync_command_mapping.py",
                )
