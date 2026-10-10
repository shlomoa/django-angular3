"""Tests for external-tool acquisition helpers."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from django_angular3.tools import (
    OasdiffUnavailableError,
    ensure_oasdiff,
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


class EnsureOasdiffTests(unittest.TestCase):
    """Verify ensure_oasdiff fails with a cause and a remedy."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.bin_dir = Path(self._tmp.name) / ".bin"
        patcher = patch("django_angular3.tools.BIN_DIR", self.bin_dir)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_download_failure_names_cause_and_remedy(self) -> None:
        with (
            patch(
                "django_angular3.tools.get_system_info",
                return_value=("linux", "amd64"),
            ),
            patch("django_angular3.tools.shutil.which", return_value=None),
            patch(
                "django_angular3.tools.urllib.request.urlopen",
                side_effect=OSError("HTTP Error 403: Forbidden"),
            ),
            patch("builtins.print"),
        ):
            with self.assertRaises(OasdiffUnavailableError) as raised:
                ensure_oasdiff()

        message = str(raised.exception)
        self.assertIn("403", message)
        self.assertIn(str(self.bin_dir / "oasdiff"), message)
        self.assertIn("PATH", message)
        self.assertIn("api.github.com", message)

    def test_unsupported_platform_states_it_and_the_remedy(self) -> None:
        with (
            patch(
                "django_angular3.tools.get_system_info",
                return_value=("macos", "arm64"),
            ),
            patch("django_angular3.tools.shutil.which", return_value=None),
            patch("django_angular3.tools.urllib.request.urlopen") as urlopen,
        ):
            with self.assertRaises(OasdiffUnavailableError) as raised:
                ensure_oasdiff()

        urlopen.assert_not_called()
        message = str(raised.exception)
        self.assertIn("Linux or Windows", message)
        self.assertIn("macos arm64", message)
        self.assertIn("PATH", message)

    def test_uses_oasdiff_on_path_before_downloading(self) -> None:
        with (
            patch(
                "django_angular3.tools.get_system_info",
                return_value=("macos", "arm64"),
            ),
            patch(
                "django_angular3.tools.shutil.which",
                return_value="/opt/bin/oasdiff",
            ),
            patch("django_angular3.tools.urllib.request.urlopen") as urlopen,
        ):
            self.assertEqual(ensure_oasdiff(), "/opt/bin/oasdiff")

        urlopen.assert_not_called()
