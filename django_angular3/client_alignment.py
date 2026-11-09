"""Terminal check: the generated Angular client matches the exported OpenAPI contract.

FR-10 of ``doc/requirements/APP_BUILDER_REQUIREMENTS.md`` makes the alignment of the
generated client with the exported OpenAPI contract part of the global acceptance of a
build. This check is deterministic and needs no process: every schema of
``components.schemas`` that the generator emits must be declared in the generated
models, and every operation (``operationId``) must have a method in the generated
services. ``ng-openapi-gen`` skips a schema that no operation reaches through a
``$ref`` unless its configuration sets ``ignoreUnusedModels`` to ``false``; the check
expects exactly what the generator emits. Both are read from the
files ``ng-openapi-gen`` wrote below the ``output`` of ``ng-openapi-gen.json``. Without
that file the project has no generated client and there is nothing to align.
``build_app`` runs it as a step before the ``last-check`` gate, so that the gate stays
the last step.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Final

from .command_translation import AppBuildStep
from .config import ProjectConfig
from .documents import DocumentError, load_document

CLIENT_ALIGNMENT_COMMAND: Final = "check_client_alignment"
CLIENT_ALIGNMENT_STEP: Final = "client-alignment"
#: With the site sources (11), before the terminal gate (12).
CLIENT_ALIGNMENT_ORDER: Final = 11
_METHODS: Final = ("get", "put", "post", "delete", "options", "head", "patch", "trace")
_DECLARATION = re.compile(
    r"export\s+(?:declare\s+)?(?:interface|type|enum|const|class)\s+(\w+)"
)
_IDENTIFIER = re.compile(r"[A-Za-z_]\w*")


def with_client_alignment_step(
    steps: tuple[AppBuildStep, ...],
) -> tuple[AppBuildStep, ...]:
    """Insert the check before the terminal gate; ``steps`` unchanged when empty."""
    if not steps:
        return steps
    step = AppBuildStep(
        name_id=CLIENT_ALIGNMENT_STEP,
        exec_order=CLIENT_ALIGNMENT_ORDER,
        change_op="validate",
        change_reason=(
            "Verify that the generated Angular client matches the exported OpenAPI "
            "contract."
        ),
        change_target="artifacts.openapiSchema",
        change_domain=None,
        command=CLIENT_ALIGNMENT_COMMAND,
        parameters={},
    )
    index = next(
        (i for i, s in enumerate(steps) if s.name_id == "last-check"), len(steps)
    )
    return (*steps[:index], step, *steps[index:])


def check_client_alignment(project_config: ProjectConfig) -> tuple[list[str], str]:
    """The misalignments (empty when aligned) and a one-line summary."""
    generator = project_config.angular_workspace / "ng-openapi-gen.json"
    if not generator.is_file():
        return [], "no ng-openapi-gen.json: no generated client to align"
    try:
        generator_config = json.loads(generator.read_text(encoding="utf-8"))
        output = project_config.angular_workspace / str(
            generator_config.get("output", "")
        )
        document = load_document(project_config.openapi_schema)
    except (OSError, ValueError, DocumentError) as exc:
        return [f"cannot read the client or the contract: {exc}"], "unreadable"
    schemas = _schemas(document)
    if generator_config.get("ignoreUnusedModels", True) is not False:
        reached = _reached_schemas(document)
        schemas = [name for name in schemas if name in reached]
    operations = _operations(document)
    declared = _declared(output / "models")
    methods = _identifiers(output)
    errors = [
        f"schema {name} has no generated model"
        for name in schemas
        if name not in declared
    ]
    errors += [
        f"operation {operation_id} has no generated service method"
        for operation_id in operations
        if _normalize(operation_id) not in methods
    ]
    summary = f"{len(schemas)} schema(s) and {len(operations)} operation(s) checked"
    return errors, summary


def _schemas(document: Any) -> list[str]:
    components = document.get("components") if isinstance(document, dict) else None
    schemas = components.get("schemas") if isinstance(components, dict) else None
    return sorted(schemas) if isinstance(schemas, dict) else []


_REFERENCE = re.compile(r"^#/components/([^/]+)/(.+)$")


def _reached_schemas(document: Any) -> set[str]:
    """Schemas an operation reaches through ``$ref``, transitively."""
    components = document.get("components") if isinstance(document, dict) else None
    components = components if isinstance(components, dict) else {}
    pending: list[Any] = [document.get("paths") if isinstance(document, dict) else None]
    seen: set[tuple[str, str]] = set()
    while pending:
        node = pending.pop()
        if isinstance(node, dict):
            reference = node.get("$ref")
            if isinstance(reference, str) and (m := _REFERENCE.match(reference)):
                name = m.group(2).split("/")[0].replace("~1", "/").replace("~0", "~")
                key = (m.group(1), name)
                if key not in seen:
                    seen.add(key)
                    section = components.get(key[0])
                    if isinstance(section, dict):
                        pending.append(section.get(name))
            pending.extend(node.values())
        elif isinstance(node, list):
            pending.extend(node)
    return {name for kind, name in seen if kind == "schemas"}


def _operations(document: Any) -> list[str]:
    paths = document.get("paths") if isinstance(document, dict) else None
    found: list[str] = []
    for item in (paths or {}).values():
        if not isinstance(item, dict):
            continue
        for method in _METHODS:
            operation = item.get(method)
            if isinstance(operation, dict) and operation.get("operationId"):
                found.append(str(operation["operationId"]))
    return sorted(found)


def _declared(models: Path) -> set[str]:
    names: set[str] = set()
    for path in sorted(models.rglob("*.ts")) if models.is_dir() else []:
        names.update(_DECLARATION.findall(path.read_text(encoding="utf-8")))
    return names


def _identifiers(output: Path) -> set[str]:
    """Identifiers of the generated services and operation functions (not models)."""
    found: set[str] = set()
    models = output / "models"
    for path in sorted(output.rglob("*.ts")) if output.is_dir() else []:
        if models in path.parents:
            continue
        text = path.read_text(encoding="utf-8")
        found.update(_normalize(word) for word in _IDENTIFIER.findall(text))
    return found


def _normalize(name: str) -> str:
    """``customers_list`` and ``customersList`` compare equal."""
    return re.sub(r"[^A-Za-z0-9]", "", name).lower()
