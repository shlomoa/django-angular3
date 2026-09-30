import io
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import django
from django.core.management import CommandError, call_command

from tests.workspace_temp import WORKSPACE_TEMP_DIR

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.test_settings")
django.setup()


class CleanupCommandTests(unittest.TestCase):
    def test_clean_removes_temporary_build_and_package_artifacts(self) -> None:
        with tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR) as temporary_directory:
            root = Path(temporary_directory)
            artifacts = (
                root / "build",
                root / "dist",
                root / ".eggs",
                root / ".pytest_cache",
                root / ".mypy_cache",
                root / ".ruff_cache",
                root / "docs" / "_build",
                root / "package.egg-info",
                root / "package" / "__pycache__",
            )
            for artifact in artifacts:
                artifact.mkdir(parents=True)
            source_file = root / "package" / "source.py"
            source_file.write_text("source", encoding="utf-8")

            with patch(
                "django_angular3.management.commands.clean.project_root",
                return_value=root,
            ):
                call_command("clean")

            self.assertTrue(source_file.exists())
            for artifact in artifacts:
                self.assertFalse(artifact.exists())

    def test_clean_dry_run_does_not_remove_artifacts(self) -> None:
        with tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR) as temporary_directory:
            root = Path(temporary_directory)
            artifact = root / "dist"
            artifact.mkdir()
            stdout = io.StringIO()

            with patch(
                "django_angular3.management.commands.clean.project_root",
                return_value=root,
            ):
                call_command("clean", dry_run=True, stdout=stdout)

            self.assertTrue(artifact.exists())
            self.assertIn(str(artifact), stdout.getvalue())

    def test_distclean_removes_untracked_files_and_preserves_tracked_files(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR) as temporary_directory:
            root = Path(temporary_directory)
            subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
            tracked_file = root / "tracked.txt"
            tracked_file.write_text("tracked", encoding="utf-8")
            subprocess.run(["git", "add", "tracked.txt"], cwd=root, check=True)
            untracked_directory = root / "untracked"
            untracked_directory.mkdir()
            (untracked_directory / "file.txt").write_text("untracked", encoding="utf-8")

            with patch(
                "django_angular3.management.commands.distclean.project_root",
                return_value=root,
            ):
                call_command("distclean")

            self.assertTrue(tracked_file.exists())
            self.assertFalse(untracked_directory.exists())

    def test_distclean_dry_run_does_not_remove_untracked_files(self) -> None:
        with tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR) as temporary_directory:
            root = Path(temporary_directory)
            subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
            untracked_file = root / "untracked.txt"
            untracked_file.write_text("untracked", encoding="utf-8")
            stdout = io.StringIO()

            with patch(
                "django_angular3.management.commands.distclean.project_root",
                return_value=root,
            ):
                call_command("distclean", dry_run=True, stdout=stdout)

            self.assertTrue(untracked_file.exists())
            self.assertIn("untracked.txt", stdout.getvalue())

    def test_distclean_reports_non_git_directory_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            with (
                patch(
                    "django_angular3.management.commands.distclean.project_root",
                    return_value=Path(temporary_directory),
                ),
                self.assertRaisesRegex(CommandError, "not a git repository"),
            ):
                call_command("distclean")
