"""The site's own source files are copied into the application project by build_app."""

import json
import unittest
from pathlib import Path

from django.core.management.base import CommandError

from django_angular3.config import ConfigError
from django_angular3.site_sources import (
    SITE_SOURCES_COMMAND,
    SiteSourcesError,
    copy_site_sources,
    validate_site_sources,
    with_site_sources_step,
)
from tests.test_step_execution import EVIDENCE_FILE_NAME, Configuration, _Project
from tests.tool_config import use_tool_configuration_template


def setUpModule() -> None:
    use_tool_configuration_template()


class SiteSourcesTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.project = _Project(self)
        self.sources = self.project.root / "site"
        (self.sources / "auth").mkdir(parents=True)
        (self.sources / "auth" / "auth.guard.ts").write_text("guard", encoding="utf-8")
        (self.sources / "app.config.ts").write_text("site config", encoding="utf-8")

    def configure(self, value: str | None = "site") -> None:
        path = self.project.config.project_config.config_path
        document = json.loads(path.read_text(encoding="utf-8"))
        if value is not None:
            document["artifacts"]["angularSiteSources"] = value
        path.write_text(json.dumps(document), encoding="utf-8")
        self.project.project_config = Configuration(path).project_config

    def steps(self, dry_run: bool = True) -> list[dict]:
        report = json.loads(
            self.project.run_build(self.project.change_set(), dry_run=dry_run)
            if dry_run
            else "{}"
        )
        return report["steps"]

    @property
    def destination(self) -> Path:
        return self.project.workspace / "projects" / "shop" / "src" / "app"


class ConfigurationTests(SiteSourcesTestCase):
    def test_the_key_is_resolved_relative_to_the_configuration(self) -> None:
        self.configure("site")

        self.assertEqual(
            self.project.project_config.angular_site_sources,
            self.sources.resolve(),
        )

    def test_without_the_key_nothing_is_configured(self) -> None:
        self.configure(None)

        self.assertIsNone(self.project.project_config.angular_site_sources)

    def test_the_key_must_be_a_string(self) -> None:
        path = self.project.config.project_config.config_path
        document = json.loads(path.read_text(encoding="utf-8"))
        document["artifacts"]["angularSiteSources"] = 3
        path.write_text(json.dumps(document), encoding="utf-8")

        with self.assertRaises(ConfigError):
            Configuration(path)


class DryRunTests(SiteSourcesTestCase):
    def test_the_copy_step_sits_between_the_last_generating_step_and_the_gate(
        self,
    ) -> None:
        self.configure("site")

        steps = self.steps()

        names = [s["step"] for s in steps]
        self.assertEqual(names[-3:], ["site-sources", "client-alignment", "last-check"])
        step = steps[-3]
        self.assertEqual(step["command"], SITE_SOURCES_COMMAND)
        self.assertEqual(step["parameters"]["source"], str(self.sources.resolve()))
        self.assertEqual(step["parameters"]["destination"], str(self.destination))
        self.assertTrue(
            steps[-4]["stage"] < step["stage"] < steps[-1]["stage"],
            "the copy runs after the generating steps and before the gate",
        )

    def test_without_the_key_there_is_no_copy_step(self) -> None:
        self.configure(None)

        self.assertNotIn("site-sources", [s["step"] for s in self.steps()])

    def test_a_missing_directory_fails_before_anything_runs(self) -> None:
        self.configure("missing")

        with self.assertRaisesRegex(CommandError, "is not a directory"):
            self.project.run_build(self.project.change_set())

        self.assertEqual(self.project.calls(), [])
        self.assertFalse((self.project.root / "build").exists())

    def test_an_empty_directory_is_refused(self) -> None:
        empty = self.project.root / "empty"
        (empty / "nested").mkdir(parents=True)
        self.configure("empty")

        with self.assertRaisesRegex(CommandError, "holds no files"):
            self.project.run_build(self.project.change_set(), dry_run=True)

    def test_nothing_changed_means_no_step_and_no_validation(self) -> None:
        self.configure("missing")

        self.assertEqual(with_site_sources_step((), self.project.project_config), ())


class CopyTests(SiteSourcesTestCase):
    def test_the_tree_is_copied_and_overwrites_generated_files(self) -> None:
        self.configure("site")
        (self.destination / "auth").mkdir(parents=True)
        (self.destination / "app.config.ts").write_text("generated", encoding="utf-8")

        copied = copy_site_sources(self.project.project_config)

        self.assertEqual(copied, ["app.config.ts", "auth/auth.guard.ts"])
        self.assertEqual(
            (self.destination / "app.config.ts").read_text(encoding="utf-8"),
            "site config",
        )
        self.assertEqual(
            (self.destination / "auth" / "auth.guard.ts").read_text(encoding="utf-8"),
            "guard",
        )

    def test_validation_names_the_directory(self) -> None:
        self.configure("missing")

        with self.assertRaisesRegex(SiteSourcesError, "missing"):
            validate_site_sources(self.project.project_config)

    def test_a_real_run_copies_before_the_terminal_build_and_records_it(self) -> None:
        self.configure("site")

        self.project.run_build(self.project.change_set())

        self.assertTrue((self.destination / "auth" / "auth.guard.ts").is_file())
        evidence = json.loads(
            (self.project.root / "build" / EVIDENCE_FILE_NAME).read_text("utf-8")
        )
        steps = evidence["steps"]
        copy = next(s for s in steps if s["step"] == "site-sources")
        self.assertEqual(copy["status"], "succeeded")
        self.assertIn("auth/auth.guard.ts", copy["invocations"][0]["stdout"])
        self.assertEqual(
            [s["step"] for s in steps][-3:],
            ["site-sources", "client-alignment", "last-check"],
        )
        self.assertEqual(self.project.calls()[-1][0], "build")


if __name__ == "__main__":
    unittest.main()
