import json
import os
import platform
import subprocess
import tarfile
import urllib.request
import zipfile
from collections.abc import Collection, Sequence
from pathlib import Path
from typing import Any, cast

# Base directory for storing downloaded tools relative to this package
PKG_DIR = Path(__file__).resolve().parent
BIN_DIR = PKG_DIR / ".bin"

_OASDIFF_RELEASE_API = "https://api.github.com/repos/oasdiff/oasdiff/releases/latest"
_OASDIFF_SUPPORTED_PLATFORMS = {
    "linux": {"amd64", "arm64"},
    "windows": {"amd64", "arm64"},
}


class ToolExecutionError(RuntimeError):
    """Raised when an allowlisted external tool cannot be executed."""


def ensure_command_is_allowed(
    command_name: str, command_allowlist: Collection[str]
) -> None:
    """Raise when a logical command is absent from its normalized allowlist."""
    normalized_command_name = command_name.strip().lower()
    if normalized_command_name in command_allowlist:
        return

    allowed_commands = ", ".join(command_allowlist) or "<none>"
    raise ToolExecutionError(
        f"Command '{command_name}' is not allowed. Allowed commands: "
        f"{allowed_commands}."
    )


def execute_command(argv: Sequence[str], *, cwd: Path) -> None:
    """Run one external command and normalize execution failures."""
    try:
        subprocess.run(argv, cwd=cwd, check=True)
    except FileNotFoundError as exc:
        raise ToolExecutionError(f"Command not found: {argv[0]}") from exc
    except subprocess.CalledProcessError as exc:
        raise ToolExecutionError(
            f"Command '{' '.join(argv)}' failed with exit code {exc.returncode}."
        ) from exc


def get_system_info() -> tuple[str, str]:
    """Returns normalized OS and architecture strings."""
    os_name = platform.system().lower()
    if os_name == "darwin":
        os_name = "macos"

    arch = platform.machine().lower()
    if arch in ["x86_64", "amd64"]:
        arch = "amd64"
    elif arch in ["arm64", "aarch64"]:
        arch = "arm64"
    elif arch in ["i386", "i686", "x86"]:
        arch = "386"

    return os_name, arch


def get_latest_oasdiff_release() -> dict[str, Any]:
    """Fetches the latest release info from oasdiff GitHub repository."""
    req = urllib.request.Request(
        _OASDIFF_RELEASE_API,
        headers={"User-Agent": "django-angular3"},
    )
    try:
        with urllib.request.urlopen(req) as response:
            data = cast(dict[str, Any], json.loads(response.read().decode("utf-8")))
            return data
    except Exception as e:
        raise RuntimeError(f"Failed to fetch latest oasdiff version: {e}")


def get_download_url(
    release_data: dict[str, Any], os_name: str, arch: str
) -> tuple[str, str]:
    """Finds the correct asset URL for the current OS and architecture."""
    # oasdiff release naming pattern: oasdiff_<version>_<os>_<arch>.tar.gz/zip
    # e.g., oasdiff_1.28.0_linux_amd64.tar.gz
    # e.g., oasdiff_1.28.0_windows_amd64.zip
    supported_architectures = _OASDIFF_SUPPORTED_PLATFORMS.get(os_name)
    if supported_architectures is None or arch not in supported_architectures:
        raise RuntimeError(
            "oasdiff is supported only on Linux or Windows with amd64 or arm64 "
            f"architecture; received {os_name} {arch}."
        )

    for asset in release_data.get("assets", []):
        name = asset["name"].lower()
        if os_name in name and arch in name:
            if name.endswith(".tar.gz") or name.endswith(".zip"):
                return asset["browser_download_url"], asset["name"]

    raise RuntimeError(
        f"Could not find a suitable oasdiff binary for {os_name} {arch}."
    )


def extract_archive(archive_path: Path, extract_to: Path) -> None:
    """Extracts a .zip or .tar.gz archive."""
    if archive_path.name.endswith(".zip"):
        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            zip_ref.extractall(extract_to)
    elif archive_path.name.endswith(".tar.gz"):
        with tarfile.open(archive_path, "r:gz") as tar_ref:
            if hasattr(tarfile, "data_filter"):
                tar_ref.extractall(extract_to, filter="data")
            else:
                tar_ref.extractall(extract_to)
    else:
        raise ValueError(f"Unsupported archive format: {archive_path.name}")


def ensure_oasdiff():
    """
    Ensures oasdiff is installed and available.
    Returns the absolute path to the oasdiff executable.
    """
    os_name, arch = get_system_info()
    if arch not in _OASDIFF_SUPPORTED_PLATFORMS.get(os_name, set()):
        get_download_url({"assets": []}, os_name, arch)

    BIN_DIR.mkdir(parents=True, exist_ok=True)

    exe_name = "oasdiff.exe" if os_name == "windows" else "oasdiff"
    oasdiff_path = BIN_DIR / exe_name

    if oasdiff_path.exists():
        # Check if it's executable
        if not os.access(oasdiff_path, os.X_OK):
            oasdiff_path.chmod(0o755)
        return str(oasdiff_path)

    print(f"oasdiff not found. Downloading to {BIN_DIR}...")

    try:
        release_data = get_latest_oasdiff_release()
        url, asset_name = get_download_url(release_data, os_name, arch)

        archive_path = BIN_DIR / asset_name

        print(f"Downloading from {url}...")
        urllib.request.urlretrieve(url, archive_path)

        print("Extracting...")
        extract_archive(archive_path, BIN_DIR)

        # Clean up archive
        archive_path.unlink()

        # Verify it was extracted properly
        if not oasdiff_path.exists():
            raise RuntimeError(
                f"Extraction completed, but {exe_name} was not found in {BIN_DIR}."
            )

        if os_name != "windows":
            oasdiff_path.chmod(0o755)

        print("oasdiff downloaded and ready.")
        return str(oasdiff_path)

    except Exception as e:
        raise RuntimeError(f"Failed to install oasdiff: {e}")


if __name__ == "__main__":
    # Test the downloader
    path: str = ensure_oasdiff()
    print(f"oasdiff is located at: {path}")
