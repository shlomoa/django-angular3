"""Tests for the external OpenAPI and OpenUI comparison boundaries."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from django_angular3.changes import ChangeDomain, ChangeOperation
from django_angular3.external_comparisons import (
    ExternalComparisonError,
    compare_openui_files,
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
                "django_angular3.external_comparisons.subprocess.run",
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
            capture_output=True,
            text=True,
        )

    def test_blank_oasdiff_output_means_no_difference(self) -> None:
        result = Mock(returncode=0, stdout="\n", stderr="")
        with (
            patch(
                "django_angular3.external_comparisons.ensure_oasdiff",
                return_value="oasdiff",
            ),
            patch(
                "django_angular3.external_comparisons.subprocess.run",
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
                "django_angular3.external_comparisons.subprocess.run",
                return_value=result,
            ),
            self.assertRaisesRegex(ExternalComparisonError, "valid JSON"),
        ):
            run_oasdiff_diff(Path("old.yaml"), Path("new.yaml"))


class OpenUiComparisonTranslationTests(unittest.TestCase):
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
