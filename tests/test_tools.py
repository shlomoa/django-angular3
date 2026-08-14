"""Tests for external-tool acquisition helpers."""

import subprocess
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from django_angular3.tools import (
    ToolExecutionError,
    ensure_command_is_allowed,
    execute_command,
    get_download_url,
    get_latest_oasdiff_release,
)


class OasdiffDownloadTests(unittest.TestCase):
    """Verify supported oasdiff release assets are selected deterministically."""

    RELEASE_DATA = {
        "assets": [
            {
                "name": "oasdiff_1.28.0_linux_amd64.tar.gz",
                "browser_download_url": "https://example.invalid/linux-amd64",
            },
            {
                "name": "oasdiff_1.28.0_windows_arm64.zip",
                "browser_download_url": "https://example.invalid/windows-arm64",
            },
        ]
    }

    def test_uses_canonical_oasdiff_release_api(self) -> None:
        response = MagicMock()
        response.read.return_value = b"{}"

        with patch("django_angular3.tools.urllib.request.urlopen") as urlopen:
            urlopen.return_value.__enter__.return_value = response
            get_latest_oasdiff_release()

        request = urlopen.call_args.args[0]
        self.assertEqual(
            request.full_url,
            "https://api.github.com/repos/oasdiff/oasdiff/releases/latest",
        )

    def test_selects_linux_amd64_archive(self) -> None:
        self.assertEqual(
            get_download_url(self.RELEASE_DATA, "linux", "amd64"),
            (
                "https://example.invalid/linux-amd64",
                "oasdiff_1.28.0_linux_amd64.tar.gz",
            ),
        )

    def test_selects_windows_arm64_archive(self) -> None:
        self.assertEqual(
            get_download_url(self.RELEASE_DATA, "windows", "arm64"),
            (
                "https://example.invalid/windows-arm64",
                "oasdiff_1.28.0_windows_arm64.zip",
            ),
        )

    def test_rejects_unsupported_platform(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "Linux or Windows"):
            get_download_url(self.RELEASE_DATA, "macos", "arm64")

    def test_rejects_unsupported_architecture(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "amd64 or arm64"):
            get_download_url(self.RELEASE_DATA, "linux", "386")


class ToolExecutionTests(unittest.TestCase):
    """Verify generic allowlist validation and command execution behavior."""

    def test_allowlisted_command_is_accepted_case_insensitively(self) -> None:
        ensure_command_is_allowed("NG_OPENAPI_GEN", ("ng_openapi_gen",))

    def test_non_allowlisted_command_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ToolExecutionError,
            r"Command 'ng_build' is not allowed\. Allowed commands: ng_openapi_gen\.",
        ):
            ensure_command_is_allowed("ng_build", ("ng_openapi_gen",))

    def test_execute_command_runs_in_requested_directory(self) -> None:
        with patch("django_angular3.tools.subprocess.run") as run:
            execute_command(("tool", "argument"), cwd=Path("workspace"))

        run.assert_called_once_with(
            ("tool", "argument"),
            cwd=Path("workspace"),
            check=True,
        )

    def test_execute_command_normalizes_process_failure(self) -> None:
        process_error = subprocess.CalledProcessError(7, ("tool", "argument"))
        with (
            patch(
                "django_angular3.tools.subprocess.run",
                side_effect=process_error,
            ),
            self.assertRaisesRegex(
                ToolExecutionError,
                r"Command 'tool argument' failed with exit code 7\.",
            ),
        ):
            execute_command(("tool", "argument"), cwd=Path("workspace"))
