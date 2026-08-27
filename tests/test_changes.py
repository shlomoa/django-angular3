"""Tests for the canonical immutable Change Model values."""

from __future__ import annotations

import json
import unittest

from django_angular3.changes import (
    Change,
    ChangeDomain,
    ChangeDomainResult,
    ChangeEvidence,
    ChangeOperation,
    ChangeSet,
)


def _empty_domain_results() -> dict[ChangeDomain, ChangeDomainResult]:
    return {domain: ChangeDomainResult(domain) for domain in ChangeDomain}


class ChangeTests(unittest.TestCase):
    def test_change_serialization_includes_canonical_fields(self) -> None:
        change = Change(
            domain=ChangeDomain.STATIC_CONFIG,
            subject="angular.workspace.style",
            path="/angular/workspace/style",
            operation=ChangeOperation.UPDATE,
            before="scss",
            after="css",
            affected=("ng_workspace",),
            evidence=(ChangeEvidence("django-angular3.json", location="/angular"),),
        )

        serialized = change.to_dict()

        self.assertEqual(serialized["domain"], "static_config")
        self.assertEqual(serialized["operation"], "update")
        self.assertEqual(serialized["before"], "scss")
        self.assertEqual(serialized["after"], "css")
        self.assertEqual(serialized["affected"], ["ng_workspace"])
        self.assertEqual(serialized["evidence"][0]["location"], "/angular")

    def test_rejects_non_atomic_operation(self) -> None:
        with self.assertRaises(ValueError):
            ChangeOperation("no_change")

    def test_rejects_non_json_values(self) -> None:
        with self.assertRaisesRegex(TypeError, "not JSON-compatible"):
            Change(
                domain=ChangeDomain.OPENUI,
                subject="page",
                path="/",
                operation=ChangeOperation.CREATE,
                before=None,
                after={"invalid": {"set"}},
            )


class ChangeSetTests(unittest.TestCase):
    def test_empty_domain_results_are_the_no_change_summary(self) -> None:
        change_set = ChangeSet(
            baseline={"projectConfig": "previous.json"},
            candidate={"projectConfig": "current.json"},
            domains=_empty_domain_results(),
        )

        self.assertFalse(change_set.has_changes)
        self.assertFalse(change_set.domains[ChangeDomain.OPENAPI].has_changes)
        self.assertEqual(change_set.to_dict()["summary"], {"hasChanges": False})

    def test_serializes_all_five_domains_and_computed_summary(self) -> None:
        change = Change(
            domain=ChangeDomain.PROJECT_CONFIG,
            subject="project.name",
            path="/project/name",
            operation=ChangeOperation.UPDATE,
            before="portal",
            after="updated_project",
        )
        domains = _empty_domain_results()
        domains[ChangeDomain.PROJECT_CONFIG] = ChangeDomainResult(
            ChangeDomain.PROJECT_CONFIG, (change,)
        )
        change_set = ChangeSet(
            baseline={"projectConfig": "previous.json"},
            candidate={"projectConfig": "current.json"},
            domains=domains,
        )

        serialized = change_set.to_dict()

        self.assertEqual(
            set(serialized["domains"]), {domain.value for domain in ChangeDomain}
        )
        self.assertTrue(serialized["summary"]["hasChanges"])
        self.assertEqual(json.loads(change_set.to_json()), serialized)

    def test_rejects_missing_domain_result(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing domain result"):
            ChangeSet(
                baseline={},
                candidate={},
                domains={
                    ChangeDomain.OPENAPI: ChangeDomainResult(ChangeDomain.OPENAPI)
                },
            )

    def test_rejects_change_in_wrong_domain_result(self) -> None:
        change = Change(
            domain=ChangeDomain.OPENAPI,
            subject="GET /customers",
            path="/",
            operation=ChangeOperation.CREATE,
            before=None,
            after={},
        )
        with self.assertRaisesRegex(ValueError, "belong to its domain"):
            ChangeDomainResult(ChangeDomain.OPENUI, (change,))
