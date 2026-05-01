"""
Pre-flight checks for the ng-workspace Create mode.

Usage:
    python scripts/preflight.py <path-to-django-angular3.json>

Exits 0 on success, 1 on failure.
Prints a line per check: PASS or FAIL with a short message.
"""
from __future__ import annotations

import json
import subprocess
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

    # 1. Config file exists
    cfg = Path(config_path)
    if not check("django-angular3.json exists", cfg.is_file(), str(cfg)):
        return 1

    # 2. Config is parseable JSON
    try:
        data = json.loads(cfg.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        check("django-angular3.json is valid JSON", False, str(exc))
        return 1
    check("django-angular3.json is valid JSON", True)

    # 3. angular.output is present
    angular_output_raw = (data.get("angular") or {}).get("output")
    if not check("angular.output key present", bool(angular_output_raw)):
        passed = False

    if angular_output_raw:
        output_dir = Path(angular_output_raw)
        if not output_dir.is_absolute():
            output_dir = cfg.parent / angular_output_raw

        # 4. Output directory does not exist or is empty
        if output_dir.exists():
            contents = list(output_dir.iterdir())
            ok = len(contents) == 0
            passed = check(
                "angular.output is empty or absent",
                ok,
                f"{output_dir} has {len(contents)} item(s)" if not ok else str(output_dir),
            ) and passed
        else:
            check("angular.output is empty or absent", True, f"{output_dir} does not exist")

    # 5. django-admin ng_new --help succeeds (djng reachable)
    try:
        result = subprocess.run(
            ["django-admin", "ng_new", "--help"],
            capture_output=True,
            timeout=15,
        )
        passed = check(
            "django-admin ng_new reachable",
            result.returncode == 0,
            "" if result.returncode == 0 else result.stderr.decode(errors="replace").strip(),
        ) and passed
    except FileNotFoundError:
        check("django-admin ng_new reachable", False, "django-admin not found in PATH")
        passed = False
    except subprocess.TimeoutExpired:
        check("django-admin ng_new reachable", False, "timed out")
        passed = False

    return 0 if passed else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path-to-django-angular3.json>", file=sys.stderr)
        sys.exit(1)
    sys.exit(main(sys.argv[1]))
