"""Regenerate the ngdj command-mapping fixture from an angular-django2 checkout.

Usage: python tests/fixtures/ngdj/sync_command_mapping.py <angular-django2 package dir>

The package dir is ``projects/angular-django2`` of the repository (or an installed
``node_modules/angular-django2``). The mapping and its schema are copied unchanged, and
``package.json`` keeps only the name and version the loader reads. The fixture is
generated, never edited by hand.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

FIXTURE_DIR = Path(__file__).resolve().parent


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    package_dir = Path(argv[1])
    package = json.loads((package_dir / "package.json").read_text(encoding="utf-8"))
    for name in ("command-mapping.json", "command-mapping.schema.json"):
        shutil.copyfile(package_dir / "schematics" / name, FIXTURE_DIR / name)
    minimal = {"name": package["name"], "version": package["version"]}
    (FIXTURE_DIR / "package.json").write_text(
        json.dumps(minimal, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Synced {package['name']}@{package['version']} into {FIXTURE_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
