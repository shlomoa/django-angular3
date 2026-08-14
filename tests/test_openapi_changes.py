"""Tests for strict OpenAPI oasdiff detail translation."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from django_angular3.changes import ChangeOperation
from django_angular3.openapi_changes import (
    OpenApiComparisonError,
    compare_openapi_files,
    translate_oasdiff_detail,
)


def _document(summary: str = "List pets") -> dict[str, object]:
    return {
        "openapi": "3.1.0",
        "paths": {
            "/pets": {"get": {"summary": summary}},
            "/owners": {"get": {"summary": "List owners"}},
        },
        "components": {
            "schemas": {"Pet": {"type": "object"}, "Owner": {"type": "object"}}
        },
    }


class OasdiffDetailTranslationTests(unittest.TestCase):
    def test_translates_path_operation_and_schema_changes_with_evidence(self) -> None:
        reference = _document()
        candidate = _document(summary="Find pets")
        candidate["paths"]["/new"] = {"post": {"summary": "Create pet"}}  # type: ignore[index]
        candidate["components"]["schemas"]["NewPet"] = {  # type: ignore[index]
            "type": "string"
        }
        detail = {
            "paths": {
                "added": ["/new"],
                "deleted": [],
                "modified": {
                    "/pets": {
                        "operations": {
                            "added": [],
                            "deleted": [],
                            "modified": {
                                "GET": {
                                    "summary": {
                                        "from": "List pets",
                                        "to": "Find pets",
                                    }
                                }
                            },
                        }
                    }
                },
            },
            "components": {
                "schemas": {"added": ["NewPet"], "deleted": [], "modified": {}}
            },
        }

        changes = translate_oasdiff_detail(
            detail, reference, candidate, source="candidate.yaml"
        )

        self.assertEqual(
            [change.operation for change in changes],
            [ChangeOperation.CREATE, ChangeOperation.UPDATE, ChangeOperation.CREATE],
        )
        self.assertEqual(changes[1].subject, "operation:GET /pets")
        self.assertEqual(changes[1].path, "/paths/~1pets/get")
        self.assertEqual(changes[1].evidence[0].source, "candidate.yaml")
        self.assertEqual(changes[2].subject, "schema:NewPet")

    def test_rejects_unknown_oasdiff_detail_instead_of_suppressing_it(self) -> None:
        with self.assertRaisesRegex(OpenApiComparisonError, "unsupported key"):
            translate_oasdiff_detail(
                {"info": {}}, _document(), _document(), source="new.yaml"
            )

    def test_translates_delete_changes_and_sparse_supported_detail(self) -> None:
        reference = _document()
        candidate = _document()
        del candidate["paths"]["/owners"]  # type: ignore[index]
        del candidate["components"]["schemas"]["Owner"]  # type: ignore[index]

        changes = translate_oasdiff_detail(
            {
                "paths": {"deleted": ["/owners"]},
                "components": {"schemas": {"deleted": ["Owner"]}},
            },
            reference,
            candidate,
            source="candidate.yaml",
        )

        self.assertEqual(
            [change.operation for change in changes],
            [ChangeOperation.DELETE, ChangeOperation.DELETE],
        )
        self.assertEqual(
            [change.subject for change in changes], ["path:/owners", "schema:Owner"]
        )

    def test_missing_baseline_creates_candidate_paths_and_schemas(self) -> None:
        candidate = _document()
        with patch(
            "django_angular3.openapi_changes._load_openapi_document",
            return_value=candidate,
        ):
            changes = compare_openapi_files(None, Path("candidate.yaml"))

        self.assertTrue(changes)
        self.assertTrue(
            all(change.operation is ChangeOperation.CREATE for change in changes)
        )
        self.assertEqual(
            {change.subject for change in changes},
            {"path:/owners", "path:/pets", "schema:Owner", "schema:Pet"},
        )
