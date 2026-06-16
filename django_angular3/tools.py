import json
import os
import platform
import tarfile
import urllib.request
import zipfile
from pathlib import Path

# Base directory for storing downloaded tools relative to this package
PKG_DIR = Path(__file__).resolve().parent
BIN_DIR = PKG_DIR / ".bin"


def get_system_info():
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


def get_latest_oasdiff_release():
    """Fetches the latest release info from oasdiff GitHub repository."""
    url = "https://api.github.com/repos/Tufin/oasdiff/releases/latest"
    req = urllib.request.Request(url, headers={"User-Agent": "django-angular3"})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data
    except Exception as e:
        raise RuntimeError(f"Failed to fetch latest oasdiff version: {e}")


def get_download_url(release_data, os_name, arch):
    """Finds the correct asset URL for the current OS and architecture."""
    # oasdiff release naming pattern: oasdiff_<version>_<os>_<arch>.tar.gz/zip
    # e.g., oasdiff_1.21.3_linux_amd64.tar.gz
    # e.g., oasdiff_1.21.3_windows_amd64.zip

    # Map our normalized OS name to oasdiff's naming conventions
    # sometimes they use darwin, sometimes macos.
    search_os = "darwin" if os_name == "macos" else os_name

    # In recent versions, windows is windows, linux is linux.

    for asset in release_data.get("assets", []):
        name = asset["name"].lower()
        if search_os in name and arch in name:
            if name.endswith(".tar.gz") or name.endswith(".zip"):
                return asset["browser_download_url"], asset["name"]

    raise RuntimeError(
        f"Could not find a suitable oasdiff binary for {os_name} {arch}."
    )


def extract_archive(archive_path, extract_to):
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
    BIN_DIR.mkdir(parents=True, exist_ok=True)

    exe_name = "oasdiff.exe" if platform.system().lower() == "windows" else "oasdiff"
    oasdiff_path = BIN_DIR / exe_name

    if oasdiff_path.exists():
        # Check if it's executable
        if not os.access(oasdiff_path, os.X_OK):
            oasdiff_path.chmod(0o755)
        return str(oasdiff_path)

    print(f"oasdiff not found. Downloading to {BIN_DIR}...")

    try:
        os_name, arch = get_system_info()
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
    path = ensure_oasdiff()
    print(f"oasdiff is located at: {path}")
