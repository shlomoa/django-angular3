"""Tests for the external OpenAPI and OpenUI comparison boundaries."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from openui_spec import compare as upstream_compare_openui_spec

import django_angular3.external_comparisons as external_comparisons
from django_angular3.changes import Change, ChangeDomain, ChangeOperation
from django_angular3.external_comparisons import (
    ExternalComparisonError,
    OpenUiElement,
    compare_openui_files,
    openui_change_elements,
    openui_create_changes,
    run_oasdiff_diff,
    translate_openui_changelog,
)
from tests.workspace_temp import WORKSPACE_TEMP_DIR

ROOT = Path(__file__).resolve().parent.parent


class OasdiffComparisonTests(unittest.TestCase):
    def test_invokes_oasdiff_with_reference_candidate_and_json_output(self) -> None:
        result = Mock(returncode=0, stdout='{"paths": {}}', stderr="")
        with (
            patch(
                "django_angular3.external_comparisons.ensure_oasdiff",
                return_value="oasdiff",
            ),
            patch(
                "django_angular3.command_execution.subprocess.run",
                return_value=result,
            ) as run,
        ):
            output = run_oasdiff_diff(Path("reference.yaml"), Path("candidate.yaml"))

        self.assertEqual(output, {"paths": {}})
        run.assert_called_once_with(
            [
                "oasdiff",
                "diff",
                "reference.yaml",
                "candidate.yaml",
                "--format",
                "json",
            ],
            cwd=None,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_blank_oasdiff_output_means_no_difference(self) -> None:
        result = Mock(returncode=0, stdout="\n", stderr="")
        with (
            patch(
                "django_angular3.external_comparisons.ensure_oasdiff",
                return_value="oasdiff",
            ),
            patch(
                "django_angular3.command_execution.subprocess.run",
                return_value=result,
            ),
        ):
            self.assertEqual(run_oasdiff_diff(Path("old.yaml"), Path("new.yaml")), {})

    def test_rejects_invalid_oasdiff_json(self) -> None:
        result = Mock(returncode=0, stdout="not json", stderr="")
        with (
            patch(
                "django_angular3.external_comparisons.ensure_oasdiff",
                return_value="oasdiff",
            ),
            patch(
                "django_angular3.command_execution.subprocess.run",
                return_value=result,
            ),
            self.assertRaisesRegex(ExternalComparisonError, "valid JSON"),
        ):
            run_oasdiff_diff(Path("old.yaml"), Path("new.yaml"))


class OpenUiComparisonTranslationTests(unittest.TestCase):
    def test_imports_compare_from_supported_openui_spec_package(self) -> None:
        self.assertIs(
            external_comparisons.compare_openui_spec,
            upstream_compare_openui_spec,
        )

    def test_uses_upstream_identity_aware_comparison_for_reordered_children(
        self,
    ) -> None:
        reference = json.loads(
            (
                ROOT
                / "tests"
                / "fixtures"
                / "artifacts"
                / "openui"
                / "example.openui.json"
            ).read_text(encoding="utf-8")
        )
        reference["children"].append({"id": "customerList", "type": "List"})
        candidate = json.loads(json.dumps(reference))
        candidate["children"].reverse()

        with tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR) as directory:
            reference_path = Path(directory) / "reference.json"
            candidate_path = Path(directory) / "candidate.json"
            reference_path.write_text(json.dumps(reference), encoding="utf-8")
            candidate_path.write_text(json.dumps(candidate), encoding="utf-8")

            self.assertEqual(compare_openui_files(reference_path, candidate_path), ())

    def test_translates_upstream_changelog_categories_to_atomic_changes(self) -> None:
        changes = translate_openui_changelog(
            {
                "remove": [{"path": "/obsolete", "reference": True}],
                "add": [{"path": "/children/page", "new": {"id": "page"}}],
                "change": [{"path": "/attrs/title", "reference": "Old", "new": "New"}],
            },
            source="candidate.openui.json",
        )

        self.assertEqual(
            [change.operation for change in changes],
            [ChangeOperation.DELETE, ChangeOperation.CREATE, ChangeOperation.UPDATE],
        )
        self.assertTrue(all(change.domain is ChangeDomain.OPENUI for change in changes))
        self.assertEqual(changes[1].path, "/children/page")
        self.assertEqual(
            changes[2].evidence[0].fragment,
            {
                "path": "/attrs/title",
                "reference": "Old",
                "new": "New",
            },
        )

    def test_rejects_unsupported_openui_changelog_shape(self) -> None:
        with self.assertRaisesRegex(ExternalComparisonError, "unsupported shape"):
            translate_openui_changelog(
                {
                    "remove": [],
                    "add": [{"path": "/page", "new": {}, "extra": True}],
                    "change": [],
                },
                source="candidate.openui.json",
            )


def _element_documents() -> tuple[dict[str, object], dict[str, object]]:
    """Small reference and candidate documents for path-resolution tests."""
    reference: dict[str, object] = {
        "id": "root",
        "type": "Application",
        "children": [
            {
                "id": "form",
                "type": "Form",
                "children": [{"id": "email", "type": "input"}],
            },
            {"id": "a/b", "type": "EmptyPage"},
        ],
    }
    return reference, json.loads(json.dumps(reference))


class OpenUiElementEvidenceTests(unittest.TestCase):
    def translate(
        self, changelog: dict[str, list[dict[str, object]]], **documents: object
    ) -> tuple[Change, ...]:
        return translate_openui_changelog(
            {"remove": [], "add": [], "change": [], **changelog},
            source="candidate.openui.json",
            **documents,
        )

    def test_a_nested_attribute_change_lists_every_enclosing_element(self) -> None:
        reference, candidate = _element_documents()

        (change,) = self.translate(
            {
                "change": [
                    {
                        "path": "/children/form/children/email/attrs/uses.label",
                        "reference": '"A"',
                        "new": '"B"',
                    }
                ]
            },
            reference=reference,
            candidate=candidate,
        )

        self.assertEqual(
            openui_change_elements(change),
            (
                OpenUiElement("root", "Application", ""),
                OpenUiElement("form", "Form", "/children/form"),
                OpenUiElement("email", "input", "/children/form/children/email"),
            ),
        )
        self.assertEqual(change.subject, "openui:" + change.path)
        self.assertEqual(change.evidence[0].fragment["path"], change.path)

    def test_an_added_element_is_its_own_nearest_element(self) -> None:
        reference, candidate = _element_documents()
        candidate["children"].append({"id": "settings", "type": "EmptyPage"})

        (change,) = self.translate(
            {"add": [{"path": "/children/settings", "new": {"id": "settings"}}]},
            reference=reference,
            candidate=candidate,
        )

        self.assertEqual(
            openui_change_elements(change)[-1],
            OpenUiElement("settings", "EmptyPage", "/children/settings"),
        )

    def test_a_removed_element_is_read_from_the_reference_document(self) -> None:
        reference, candidate = _element_documents()
        candidate["children"][0]["children"].clear()

        (change,) = self.translate(
            {
                "remove": [
                    {
                        "path": "/children/form/children/email",
                        "reference": {"id": "email"},
                    }
                ]
            },
            reference=reference,
            candidate=candidate,
        )

        self.assertEqual(
            [element.id for element in openui_change_elements(change)],
            ["root", "form", "email"],
        )

    def test_a_member_or_child_list_belongs_to_its_owning_element(self) -> None:
        reference, candidate = _element_documents()

        changes = self.translate(
            {
                "add": [{"path": "/attrs", "new": {"uses.title": '"X"'}}],
                "remove": [{"path": "/children/form/children", "reference": []}],
                "change": [
                    {
                        "path": "/children/form/type",
                        "reference": "Form",
                        "new": "Grid",
                    }
                ],
            },
            reference=reference,
            candidate=candidate,
        )

        self.assertEqual(
            {change.path: openui_change_elements(change)[-1].id for change in changes},
            {
                "/attrs": "root",
                "/children/form/children": "form",
                "/children/form/type": "form",
            },
        )

    def test_an_escaped_element_id_is_resolved_and_the_pointer_kept(self) -> None:
        reference, candidate = _element_documents()

        (change,) = self.translate(
            {"change": [{"path": "/children/a~1b/attrs", "reference": 1, "new": 2}]},
            reference=reference,
            candidate=candidate,
        )

        self.assertEqual(
            openui_change_elements(change)[-1],
            OpenUiElement("a/b", "EmptyPage", "/children/a~1b"),
        )

    def test_a_path_naming_no_element_is_rejected(self) -> None:
        reference, candidate = _element_documents()

        with self.assertRaisesRegex(ExternalComparisonError, "names no element 'gone'"):
            self.translate(
                {
                    "change": [
                        {"path": "/children/gone/attrs", "reference": 1, "new": 2}
                    ]
                },
                reference=reference,
                candidate=candidate,
            )

    def test_changes_derived_without_documents_carry_no_element_evidence(self) -> None:
        (change,) = self.translate(
            {"change": [{"path": "/attrs/title", "reference": "A", "new": "B"}]}
        )

        self.assertEqual(openui_change_elements(change), ())
        self.assertEqual(len(change.evidence), 1)

    def test_one_document_without_the_other_is_rejected(self) -> None:
        reference, _ = _element_documents()

        with self.assertRaises(ValueError):
            self.translate({}, reference=reference)

    def test_file_comparison_records_the_elements_of_each_change(self) -> None:
        reference = json.loads(
            (
                ROOT
                / "tests"
                / "fixtures"
                / "artifacts"
                / "openui"
                / "example.openui.json"
            ).read_text(encoding="utf-8")
        )
        candidate = json.loads(json.dumps(reference))
        form = next(c for c in candidate["children"] if c["id"] == "inviteUserForm")
        email = next(c for c in form["children"] if c["id"] == "emailField")
        email["attrs"]["uses.label"] = json.dumps("Work email")
        form["children"] = [c for c in form["children"] if c["id"] != "submitButton"]
        candidate["children"].append({"id": "settingsPage", "type": "EmptyPage"})

        with tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR) as directory:
            reference_path = Path(directory) / "reference.json"
            candidate_path = Path(directory) / "candidate.json"
            reference_path.write_text(json.dumps(reference), encoding="utf-8")
            candidate_path.write_text(json.dumps(candidate), encoding="utf-8")

            changes = compare_openui_files(reference_path, candidate_path)

        chains = {
            change.operation: [
                (element.id, element.type) for element in openui_change_elements(change)
            ]
            for change in changes
        }
        self.assertEqual(
            chains,
            {
                ChangeOperation.DELETE: [
                    ("root", "Application"),
                    ("inviteUserForm", "Grid"),
                    ("submitButton", "ToolAction"),
                ],
                ChangeOperation.CREATE: [
                    ("root", "Application"),
                    ("settingsPage", "EmptyPage"),
                ],
                ChangeOperation.UPDATE: [
                    ("root", "Application"),
                    ("inviteUserForm", "Grid"),
                    ("emailField", "input"),
                ],
            },
        )


class OpenUiInitialBuildTests(unittest.TestCase):
    """A missing OpenUI baseline gives the create set of the candidate document."""

    DOCUMENT = {
        "id": "page",
        "type": "html",
        "attrs": {"uses.lang": "en"},
        "children": [
            {
                "id": "zeta",
                "type": "DashboardPage",
                "children": [{"id": "inner", "type": "Form"}],
            },
            {"id": "alpha", "type": "Application"},
        ],
    }

    def test_the_root_and_each_top_level_child_are_created(self) -> None:
        changes = openui_create_changes(self.DOCUMENT, source="app.openui.json")

        self.assertEqual(
            [(c.subject, c.path, c.operation) for c in changes],
            [
                ("openui:/", "", ChangeOperation.CREATE),
                ("openui:/children/alpha", "/children/alpha", ChangeOperation.CREATE),
                ("openui:/children/zeta", "/children/zeta", ChangeOperation.CREATE),
            ],
        )
        root, alpha, zeta = changes
        self.assertEqual(
            root.after,
            {"id": "page", "type": "html", "attrs": {"uses.lang": "en"}},
        )
        self.assertIsNone(root.before)
        self.assertEqual(zeta.after["children"][0]["id"], "inner")

    def test_the_changes_carry_the_enclosing_elements_like_compared_ones(self) -> None:
        root, alpha, zeta = openui_create_changes(self.DOCUMENT, source="a.json")

        self.assertEqual(
            [(e.id, e.type, e.path) for e in openui_change_elements(root)],
            [("page", "html", "")],
        )
        self.assertEqual(
            [(e.id, e.type, e.path) for e in openui_change_elements(zeta)],
            [("page", "html", ""), ("zeta", "DashboardPage", "/children/zeta")],
        )

    def test_the_child_paths_are_those_the_comparator_reports_for_an_add(self) -> None:
        empty = {"id": "page", "type": "html", "attrs": {"uses.lang": "en"}}
        added = upstream_compare_openui_spec(empty, self.DOCUMENT)["add"]

        # The comparator reports the whole children list once; its per-element form
        # is the same path grammar the create set uses for each top-level child.
        self.assertEqual([entry["path"] for entry in added], ["/children"])
        changes = openui_create_changes(self.DOCUMENT, source="a.json")
        self.assertEqual(
            [c.path for c in changes[1:]],
            [
                f"/children/{child['id']}"
                for child in sorted(
                    self.DOCUMENT["children"], key=lambda child: child["id"]
                )
            ],
        )

    def test_a_document_without_children_is_only_the_root(self) -> None:
        changes = openui_create_changes(
            {"id": "app", "type": "Application"}, source="s"
        )

        self.assertEqual([c.subject for c in changes], ["openui:/"])

    def test_the_candidate_is_validated_before_the_changes_are_derived(self) -> None:
        with tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR) as directory:
            path = Path(directory) / "app.openui.json"
            path.write_text(json.dumps({"id": "x"}), encoding="utf-8")

            with self.assertRaisesRegex(ExternalComparisonError, "Invalid OpenUI"):
                compare_openui_files(None, path)

    def test_a_file_without_a_baseline_gives_the_create_set(self) -> None:
        candidate = ROOT / "django_angular3/examples/01_simple_crm/app.openui.json"

        changes = compare_openui_files(None, candidate)

        self.assertEqual(
            [c.subject for c in changes],
            [
                "openui:/",
                "openui:/children/crmApp",
                "openui:/children/customersPage",
                "openui:/children/productsPage",
            ],
        )
        self.assertTrue(all(c.operation is ChangeOperation.CREATE for c in changes))
