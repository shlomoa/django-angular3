"""Generate ``tests/fixtures/service-names``: the real ``ng-openapi-gen`` class names.

The fixture holds the reviewed user-management contract of ``specialized-gardens``
(``gardens.schema.yaml``, copied) and a document with one operation per tag shape
(``tags.openapi.json``, built here), and for each the service classes the real
``ng-openapi-gen`` generated (``*.services.json``). All are generated, never edited by
hand::

    python -m tests.generate_service_names [--schema PATH]

It needs ``node`` and ``npm`` and installs ``ng-openapi-gen`` into a temporary
directory. ``tests/test_resource_identity.py`` checks the rule against the output.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "service-names"
GENERATOR = "ng-openapi-gen@1.1.0"
SUFFIX = "ApiService"
TAGS = ("v1", "user-management", "Users", "userProfiles", "my tag_x")


def tags_document() -> dict[str, Any]:
    """One path and operation per tag shape, plus an untagged one."""
    paths: dict[str, Any] = {}
    for index, tag in enumerate((*TAGS, None)):
        operation: dict[str, Any] = {
            "operationId": f"operation{index}",
            "responses": {"200": {"description": "ok"}},
        }
        if tag is not None:
            operation["tags"] = [tag]
        paths[f"/p{index}/"] = {"get": operation}
    return {
        "openapi": "3.0.3",
        "info": {"title": "Tags", "version": "1.0.0"},
        "paths": paths,
    }


def generated_classes(input_file: Path, work: Path) -> list[str]:
    """The service classes the real generator emits for a document."""
    output = work / f"out-{input_file.stem}"
    config = work / f"{input_file.stem}.config.json"
    config.write_text(
        json.dumps(
            {
                "input": str(input_file),
                "output": str(output),
                "services": True,
                "serviceSuffix": SUFFIX,
            }
        ),
        encoding="utf-8",
    )
    subprocess.run(
        ["npx", "--no-install", "ng-openapi-gen", "-c", str(config)],
        cwd=work,
        check=True,
        capture_output=True,
    )
    classes = [
        match
        for file in sorted((output / "services").glob("*.ts"))
        for match in re.findall(r"export class (\w+)", file.read_text("utf-8"))
    ]
    return sorted(classes)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path(__file__).resolve().parents[2]
        / "specialized-gardens"
        / "gen"
        / "source"
        / "schema.yaml",
    )
    args = parser.parse_args()
    FIXTURES.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(args.schema, FIXTURES / "gardens.schema.yaml")
    (FIXTURES / "tags.openapi.json").write_text(
        json.dumps(tags_document(), indent=2) + "\n", encoding="utf-8"
    )
    with tempfile.TemporaryDirectory() as directory:
        work = Path(directory)
        subprocess.run(["npm", "init", "-y"], cwd=work, check=True, capture_output=True)
        subprocess.run(
            ["npm", "install", GENERATOR], cwd=work, check=True, capture_output=True
        )
        for name in ("gardens.schema.yaml", "tags.openapi.json"):
            classes = generated_classes(FIXTURES / name, work)
            target = FIXTURES / f"{name.split('.')[0]}.services.json"
            target.write_text(
                json.dumps(
                    {"generator": GENERATOR, "suffix": SUFFIX, "classes": classes},
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )


if __name__ == "__main__":
    main()
