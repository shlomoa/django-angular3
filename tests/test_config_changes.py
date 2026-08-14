"""Tests for django-angular3 static and project configuration change derivation."""

from __future__ import annotations

import unittest
from copy import deepcopy
from pathlib import Path

from django_angular3.changes import ChangeDomain, ChangeOperation
from django_angular3.config import ProjectConfig
from django_angular3.config_changes import compare_project_config, compare_static_config


def _static_config(
    *, style: str = "scss", allowlist: list[str] | None = None
) -> dict[str, object]:
    return {
        "ngOpenApiGen": {"serviceSuffix": "Api", "modelIndex": True},
        "drfSpectacular": {"settings": {"TITLE": "Example", "VERSION": "1"}},
        "oasdiff": {"format": "json"},
        "angular": {
            "workspace": {"packageManager": "pnpm", "style": style, "routing": True},
            "application": {"ssr": False, "zoneless": True},
            "build": {"configuration": "production"},
        },
        "tool": {
            "executables": {"node": "node", "pnpm": "pnpm", "ng": "ng"},
            "commandAllowlist": allowlist or ["ng_openapi_gen", "ng_build"],
            "ngAddPackage": "angular-django2",
        },
    }


def _project_config(
    *, name: str = "portal", workspace: str = "build/angular"
) -> ProjectConfig:
    return ProjectConfig(
        config_path=Path("django-angular3-portal.json"),
        project_name=name,
        openapi_schema=Path("spec/openapi.json"),
        openui_specification=Path("spec/app.openui.json"),
        angular_workspace=Path(workspace),
    )


class StaticConfigComparisonTests(unittest.TestCase):
    def test_identical_static_configurations_have_no_changes(self) -> None:
        config = _static_config()

        self.assertEqual(compare_static_config(config, config), ())

    def test_static_field_update_uses_a_configuration_path(self) -> None:
        changes = compare_static_config(_static_config(), _static_config(style="css"))

        self.assertEqual(len(changes), 1)
        change = changes[0]
        self.assertEqual(change.domain, ChangeDomain.STATIC_CONFIG)
        self.assertEqual(change.operation, ChangeOperation.UPDATE)
        self.assertEqual(change.path, "/angular/workspace/style")
        self.assertEqual((change.before, change.after), ("scss", "css"))

    def test_every_mutable_supported_static_field_emits_an_update(self) -> None:
        updates = (
            (("ngOpenApiGen", "serviceSuffix"), "Client"),
            (("ngOpenApiGen", "modelIndex"), False),
            (("drfSpectacular", "settings", "TITLE"), "Updated API"),
            (("angular", "workspace", "packageManager"), "npm"),
            (("angular", "workspace", "style"), "css"),
            (("angular", "workspace", "routing"), False),
            (("angular", "application", "ssr"), True),
            (("angular", "application", "zoneless"), False),
            (("angular", "build", "configuration"), "development"),
            (("tool", "executables", "node"), "node.exe"),
            (("tool", "executables", "pnpm"), "pnpm.cmd"),
            (("tool", "executables", "ng"), "ng.cmd"),
            (("tool", "ngAddPackage"), "@example/angular-django2"),
        )
        baseline = _static_config()

        for path, value in updates:
            with self.subTest(path=path):
                candidate = deepcopy(baseline)
                target: dict[str, object] = candidate
                for token in path[:-1]:
                    target = target[token]  # type: ignore[assignment]
                target[path[-1]] = value

                changes = compare_static_config(baseline, candidate)

                self.assertEqual(len(changes), 1)
                self.assertEqual(
                    changes[0].path,
                    "/" + "/".join(path),
                )
                self.assertEqual(changes[0].operation, ChangeOperation.UPDATE)

    def test_allowlist_reordering_and_case_do_not_change_semantics(self) -> None:
        changes = compare_static_config(
            _static_config(allowlist=["ng_build", "ng_openapi_gen"]),
            _static_config(allowlist=[" NG_OPENAPI_GEN ", "ng_build"]),
        )

        self.assertEqual(changes, ())

    def test_missing_static_baseline_emits_create_changes(self) -> None:
        changes = compare_static_config(None, _static_config())

        self.assertTrue(changes)
        self.assertTrue(
            all(change.operation is ChangeOperation.CREATE for change in changes)
        )

    def test_invalid_static_config_is_rejected_before_comparison(self) -> None:
        invalid = _static_config()
        invalid.pop("tool")

        with self.assertRaisesRegex(ValueError, "Invalid django-angular3.json"):
            compare_static_config(None, invalid)

    def test_oasdiff_format_change_is_a_static_config_change(self) -> None:
        baseline = _static_config()
        candidate = _static_config()
        candidate["oasdiff"] = {"format": "yaml"}

        with self.assertRaisesRegex(ValueError, "oasdiff.format must be 'json'"):
            compare_static_config(baseline, candidate)

    def test_unknown_static_config_key_is_rejected_before_comparison(self) -> None:
        invalid = _static_config()
        invalid["unsupported"] = True

        with self.assertRaisesRegex(ValueError, "unsupported key"):
            compare_static_config(None, invalid)

    def test_unknown_nested_static_config_key_is_rejected_before_comparison(
        self,
    ) -> None:
        invalid = _static_config()
        invalid["ngOpenApiGen"]["unsupported"] = True  # type: ignore[index]

        with self.assertRaisesRegex(
            ValueError, "ngOpenApiGen contains unsupported key"
        ):
            compare_static_config(None, invalid)


class ProjectConfigComparisonTests(unittest.TestCase):
    def test_identical_project_configurations_have_no_changes(self) -> None:
        config = _project_config()

        self.assertEqual(compare_project_config(config, config), ())

    def test_project_selector_update_is_distinct_from_content_changes(self) -> None:
        changes = compare_project_config(
            _project_config(), _project_config(workspace="build/client")
        )

        self.assertEqual(len(changes), 1)
        change = changes[0]
        self.assertEqual(change.domain, ChangeDomain.PROJECT_CONFIG)
        self.assertEqual(change.operation, ChangeOperation.UPDATE)
        self.assertEqual(change.path, "/artifacts/angularWorkspace")
        self.assertEqual(
            (change.before, change.after), ("build/angular", "build/client")
        )

    def test_every_project_field_emits_a_separate_update(self) -> None:
        baseline = _project_config()
        candidates = (
            (_project_config(name="crm"), "/project/name"),
            (
                ProjectConfig(
                    config_path=baseline.config_path,
                    project_name=baseline.project_name,
                    openapi_schema=Path("spec/current.openapi.json"),
                    openui_specification=baseline.openui_specification,
                    angular_workspace=baseline.angular_workspace,
                ),
                "/artifacts/openapiSchema",
            ),
            (
                ProjectConfig(
                    config_path=baseline.config_path,
                    project_name=baseline.project_name,
                    openapi_schema=baseline.openapi_schema,
                    openui_specification=Path("spec/current.openui.json"),
                    angular_workspace=baseline.angular_workspace,
                ),
                "/artifacts/openuiSpecification",
            ),
            (_project_config(workspace="build/client"), "/artifacts/angularWorkspace"),
        )

        for candidate, path in candidates:
            with self.subTest(path=path):
                changes = compare_project_config(baseline, candidate)

                self.assertEqual(len(changes), 1)
                self.assertEqual(changes[0].path, path)
                self.assertEqual(changes[0].operation, ChangeOperation.UPDATE)

    def test_project_artifact_relocation_is_an_update(self) -> None:
        baseline = _project_config(workspace="build/angular")
        candidate = _project_config(workspace="build/relocated-angular")

        change = compare_project_config(baseline, candidate)[0]

        self.assertEqual(change.path, "/artifacts/angularWorkspace")
        self.assertEqual(change.operation, ChangeOperation.UPDATE)

    def test_missing_project_baseline_emits_all_four_selectors(self) -> None:
        changes = compare_project_config(None, _project_config())

        self.assertEqual(len(changes), 4)
        self.assertTrue(
            all(change.operation is ChangeOperation.CREATE for change in changes)
        )
