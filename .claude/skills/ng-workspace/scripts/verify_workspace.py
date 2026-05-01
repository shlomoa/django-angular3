"""
Post-creation verification for the ng-workspace Create mode.

Usage:
    python scripts/verify_workspace.py <path-to-django-angular3.json>

Exits 0 if workspace is valid, 1 if any check fails.
Prints a line per check: PASS or FAIL with a short message.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def check(label: str, ok: bool, detail: str = "") -> bool:
    status = "PASS" if ok else "FAIL"
    msg = f"{status}: {label}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    return ok


def main(config_path: str) -> int:
    passed = True

    cfg = Path(config_path)
    if not cfg.is_file():
        print(f"FAIL: django-angular3.json not found — {cfg}", file=sys.stderr)
        return 1

    try:
        data = json.loads(cfg.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"FAIL: django-angular3.json parse error — {exc}", file=sys.stderr)
        return 1

    angular_output_raw = (data.get("angular") or {}).get("output")
    if not angular_output_raw:
        print("FAIL: angular.output key missing from config", file=sys.stderr)
        return 1

    output_dir = Path(angular_output_raw)
    if not output_dir.is_absolute():
        output_dir = cfg.parent / angular_output_raw

    # 1. angular.json exists
    angular_json = output_dir / "angular.json"
    if not check("angular.json exists", angular_json.is_file(), str(angular_json)):
        return 1

    # 2. angular-django2 in cli.schematicCollections
    try:
        workspace_cfg = json.loads(angular_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        check("angular.json is valid JSON", False, str(exc))
        return 1

    collections = (
        workspace_cfg.get("cli") or {}
    ).get("schematicCollections") or []
    passed = check(
        "angular-django2 in cli.schematicCollections",
        "angular-django2" in collections,
        f"found: {collections}",
    ) and passed

    # 3. node_modules exists (packages installed)
    node_modules = output_dir / "node_modules"
    passed = check(
        "node_modules exists",
        node_modules.is_dir(),
        str(node_modules),
    ) and passed

    # 4. package.json exists
    passed = check(
        "package.json exists",
        (output_dir / "package.json").is_file(),
    ) and passed

    # 5. tsconfig.json exists
    passed = check(
        "tsconfig.json exists",
        (output_dir / "tsconfig.json").is_file(),
    ) and passed

    return 0 if passed else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path-to-django-angular3.json>", file=sys.stderr)
        sys.exit(1)
    sys.exit(main(sys.argv[1]))
