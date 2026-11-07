"""Read the upstream ngdj command mapping that ``build_app`` translation consumes.

``angular-django2`` (ngdj) ships ``schematics/command-mapping.json``: which command
compiles which OpenUI node type and which operations it supports. ngdj owns those
facts (``doc/ARCHITECTURE.md`` §3.4), so this module only locates the file in the
workspace's installed package, checks that it is the one this djng build expects and
exposes read-only accessors. It keeps no copy of the inventory.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Any, Final, cast

import openui_spec
from jsonschema import Draft202012Validator

from .settings import is_package_path, package_path

SUPPORTED_MAPPING_VERSION: Final = 1
MAPPING_FILE_NAME: Final = "command-mapping.json"
MAPPING_SCHEMA_FILE_NAME: Final = "command-mapping.schema.json"
_COMMAND_SECTIONS: Final = ("ui", "api", "tooling")


class CommandMappingError(ValueError):
    """Raised when the ngdj command mapping is missing, invalid or unexpected."""


@dataclass(frozen=True)
class OperationStatus:
    """What the mapping says about one operation on a node type or command.

    ``status`` is one of the upstream values (``supported``, ``partial``, ``indirect``,
    ``tooling-only``, ``unsupported``). ``reason`` and ``gap`` explain an unsupported or
    partial operation; ``via`` names the root node types of an ``indirect`` one.
    """

    status: str
    reason: str | None
    gap: str | None
    via: tuple[str, ...]


@dataclass(frozen=True)
class NodeCommand:
    """One command that compiles a root node type, with its selection condition."""

    command: str
    when: str | None


def parse_package_spec(spec: str) -> tuple[str, str | None]:
    """Split ``name``, ``name@version``, ``@scope/name`` or ``@scope/name@version``.

    A local package path is returned whole and unpinned; its package name is read from
    its ``package.json`` by ``load_command_mapping``.
    """
    if is_package_path(spec):
        return spec, None
    at = spec.rfind("@")
    if at <= 0:
        return spec, None
    return spec[:at], spec[at + 1 :] or None


def _spec_version(version: str) -> tuple[str, str]:
    """Major and minor of an OpenUI schema version, the spec identity."""
    parts = version.split(".")
    return parts[0], parts[1] if len(parts) > 1 else ""


def installed_openui_schema_version() -> str:
    """The OpenUI schema version declared by the installed ``openui-spec`` package.

    The package's ``SCHEMA_VERSION`` file is the sole schema-version declaration
    (openui-spec ``RELEASING.md``); it is independent of the package release
    version, and an OpenUI document declares no version of its own. The file is
    looked up in the installed distribution's record (the wheel ships it as a
    data file), as ``openui_spec`` package data, and at the root of a source
    checkout (an editable install).
    """
    candidates: list[Path] = []
    try:
        distribution = metadata.distribution("openui-spec")
    except metadata.PackageNotFoundError:
        distribution = None
    if distribution is not None:
        candidates.extend(
            Path(str(distribution.locate_file(entry)))
            for entry in distribution.files or ()
            if entry.name == "SCHEMA_VERSION"
        )
    package_dir = Path(cast(str, openui_spec.__file__)).resolve().parent
    candidates.append(package_dir / "SCHEMA_VERSION")  # openui_spec package data
    candidates.append(package_dir.parent / "SCHEMA_VERSION")  # a source checkout
    for candidate in candidates:
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8").strip()
    raise CommandMappingError(
        f"The installed openui-spec {openui_spec.__version__} ships no "
        "SCHEMA_VERSION file; install an openui-spec distribution that does."
    )


def load_command_mapping(
    workspace: Path,
    package_spec: str,
    *,
    installed_openui_spec_version: str | None = None,
) -> CommandMapping:
    """Load and check the command mapping of the ngdj package installed in a workspace.

    ``package_spec`` is the configured ``tool.ngAddPackage``. When it pins a version,
    the installed package must have exactly that version. The mapping must validate
    against the schema shipped beside it, use a supported ``mappingVersion`` and target
    the same OpenUI schema version (major and minor) as the ``SCHEMA_VERSION`` of the
    installed ``openui-spec``.
    """
    name, pinned = parse_package_spec(package_spec)
    if is_package_path(package_spec):
        name = _package_name_at(workspace / package_path(package_spec), package_spec)
    package_dir = workspace / "node_modules" / name
    schematics_dir = package_dir / "schematics"
    mapping_path = schematics_dir / MAPPING_FILE_NAME
    if not mapping_path.is_file():
        raise CommandMappingError(
            f"ngdj command mapping not found: {mapping_path}. "
            f"Install {package_spec} in the Angular workspace (ng_add)."
        )

    if pinned is not None:
        installed = _installed_package_version(package_dir)
        if installed != pinned:
            raise CommandMappingError(
                f"Installed {name} is {installed}, but tool.ngAddPackage pins {pinned}."
            )

    document = _load_json(mapping_path)
    declared_version = document.get("mappingVersion")
    if declared_version not in (None, SUPPORTED_MAPPING_VERSION):
        raise CommandMappingError(
            f"{mapping_path} has mappingVersion {declared_version}; this djng "
            f"supports {SUPPORTED_MAPPING_VERSION}."
        )
    schema = _load_json(schematics_dir / MAPPING_SCHEMA_FILE_NAME)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: [str(part) for part in error.path],
    )
    if errors:
        first = errors[0]
        location = "/" + "/".join(str(part) for part in first.path)
        raise CommandMappingError(
            f"{mapping_path} does not match {MAPPING_SCHEMA_FILE_NAME}: "
            f"{location}: {first.message}"
        )

    expected = installed_openui_spec_version or installed_openui_schema_version()
    declared = document["openuiSpecVersion"]
    if _spec_version(declared) != _spec_version(expected):
        raise CommandMappingError(
            f"{mapping_path} targets OpenUI spec {declared}, but the installed "
            f"openui-spec is {expected}."
        )
    return CommandMapping(document)


def _package_name_at(directory: Path, spec: str) -> str:
    """The package name of a local package directory (relative paths: the workspace)."""
    package_json = directory / "package.json"
    if not package_json.is_file():
        raise CommandMappingError(
            f"tool.ngAddPackage {spec} has no package.json at {directory}."
        )
    name = _load_json(package_json).get("name")
    if not isinstance(name, str) or not name:
        raise CommandMappingError(f"{package_json} has no package name.")
    return name


def _installed_package_version(package_dir: Path) -> str:
    package_json = package_dir / "package.json"
    if not package_json.is_file():
        raise CommandMappingError(
            f"Installed package has no package.json: {package_dir}."
        )
    version = _load_json(package_json).get("version")
    if not isinstance(version, str):
        raise CommandMappingError(f"{package_json} has no version.")
    return version


def _load_json(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CommandMappingError(f"Required file not found: {path}.") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise CommandMappingError(f"Cannot read {path}: {exc}.") from exc
    if not isinstance(document, dict):
        raise CommandMappingError(f"{path} must contain a JSON object.")
    return cast(dict[str, Any], document)


class CommandMapping:
    """Read-only view of a validated ngdj command mapping document."""

    def __init__(self, document: Mapping[str, Any]) -> None:
        self._document = document
        self._nodes: Mapping[str, Any] = document["ui"]["nodes"]
        self._commands: dict[str, Mapping[str, Any]] = {}
        for section in _COMMAND_SECTIONS:
            self._commands.update(document[section]["commands"])

    @property
    def mapping_version(self) -> int:
        return cast(int, self._document["mappingVersion"])

    @property
    def openui_spec_version(self) -> str:
        return cast(str, self._document["openuiSpecVersion"])

    def has_node_type(self, node_type: str) -> bool:
        return node_type in self._nodes

    def node_types(self) -> tuple[str, ...]:
        return tuple(self._nodes)

    def role(self, node_type: str) -> str:
        """``root`` (a command compiles it) or ``embedded`` (compiled with a root)."""
        return cast(str, self._node(node_type)["role"])

    def commands_for(self, node_type: str) -> tuple[NodeCommand, ...]:
        """The commands that compile a root node type, in the mapping's order."""
        return tuple(
            NodeCommand(entry["command"], entry.get("when"))
            for entry in self._node(node_type).get("commands", ())
        )

    def compiled_by(self, node_type: str) -> tuple[str, ...]:
        """The root node types that compile an embedded node type."""
        return tuple(self._node(node_type).get("compiledBy", ()))

    def operation_status(self, node_type: str, operation: str) -> OperationStatus:
        """The status of an operation (a ``ChangeOperation`` value) on a node type."""
        return _operation_status(self._node(node_type)["operations"], operation)

    def command_operation_status(self, command: str, operation: str) -> OperationStatus:
        """The status of an operation on an ngdj command of any section."""
        return _operation_status(self._command(command)["operations"], operation)

    def parameter_names(self, command: str) -> tuple[str, ...]:
        """The parameter names (``nodeId``, ``path``, ...) an ngdj command accepts."""
        return tuple(
            entry["name"] for entry in self._command(command).get("parameters", ())
        )

    def order(self, command: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
        """The commands (or tools) this one runs ``before`` and ``after``."""
        entry = self._command(command)
        return tuple(entry.get("before", ())), tuple(entry.get("after", ()))

    def on_existing(self, command: str) -> str:
        """What a second run does: ``skip``, ``reject``, ``rewrite`` and so on."""
        return cast(str, self._command(command)["onExisting"]["outcome"])

    def _node(self, node_type: str) -> Mapping[str, Any]:
        try:
            return cast(Mapping[str, Any], self._nodes[node_type])
        except KeyError:
            raise CommandMappingError(
                f"Unknown OpenUI node type: {node_type}."
            ) from None

    def _command(self, command: str) -> Mapping[str, Any]:
        try:
            return self._commands[command]
        except KeyError:
            raise CommandMappingError(f"Unknown ngdj command: {command}.") from None


def _operation_status(
    operations: Mapping[str, Mapping[str, Any]], operation: str
) -> OperationStatus:
    try:
        entry = operations[str(operation)]
    except KeyError:
        raise CommandMappingError(f"Unknown operation: {operation}.") from None
    return OperationStatus(
        status=entry["status"],
        reason=entry.get("reason"),
        gap=entry.get("gap"),
        via=tuple(entry.get("via", ())),
    )
