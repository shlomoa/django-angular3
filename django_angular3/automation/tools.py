"""Deterministic Tool implementations (``doc/contracts/TOOL_CONTRACTS.md``).

Each Tool takes a structured input object and returns a structured output object or
raises ``ContractError`` with a failure category the caller can distinguish
(``invalid_input``, ``missing_dependency``, ``external_tool_failed``,
``output_invalid``). Callers never parse raw CLI text. Every process starts through
``command_execution``; Angular tooling uses workspace-local dependencies and downloads
nothing at runtime. No provider SDK is imported here.

``tool_function`` adapts a Tool to ``DirectExecutor`` (``ToolCall``); ``invoke_tool``
returns a ``ToolResult`` directly.
"""

from __future__ import annotations

import importlib
import json
import re
import shlex
import shutil
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, Final, cast
from urllib.parse import urlsplit

from .. import angular, command_execution, tools
from ..config import ConfigError, ProjectConfig, get_previous_schema_path
from ..documents import DocumentError, load_document
from ..ngdj_command_mapping import (
    CommandMapping,
    CommandMappingError,
    load_command_mapping,
)
from ..settings import AngularCommandError, DjangoAngularSettings, load_angular_settings
from ..validation import validate_openapi_file
from .contracts import ContractError, FailureCategory, ToolResult
from .execution import ExecutionContext, ToolFunction, normalize_failure
from .migrations import write_record
from .tool_catalog import (
    CATALOG,
    ToolSpec,
    invalid,
    require_kebab_case,
    validate_inputs,
)

ToolImplementation = Callable[[ExecutionContext, Mapping[str, Any]], Mapping[str, Any]]

_IGNORED_DIRECTORIES: Final = frozenset(
    {"node_modules", ".git", "dist", ".angular", ".django-angular3", "__pycache__"}
)
_OUTPUT_TAIL: Final = 2000
_SCHEMATIC_PREFIX: Final = "angular-django2:"


# -- dispatch ---------------------------------------------------------------------


def resolve_implementation(spec: ToolSpec) -> ToolImplementation:
    """The function named by the Tool's implementation reference."""
    module_name, _, attribute = spec.implementation.partition(":")
    return cast(
        ToolImplementation, getattr(importlib.import_module(module_name), attribute)
    )


def tool_function(name: str) -> ToolFunction:
    """The Tool ``name`` as a ``ToolCall`` function: validates, then implements."""
    spec = _spec(name)

    def run(context: ExecutionContext, inputs: Mapping[str, Any]) -> Mapping[str, Any]:
        checked = validate_inputs(spec, inputs)
        return resolve_implementation(spec)(context, checked)

    return run


def invoke_tool(
    name: str, inputs: Mapping[str, Any], context: ExecutionContext
) -> ToolResult:
    """Run a Tool; the result carries its output or a structured failure."""
    try:
        output = tool_function(name)(context, inputs)
        return ToolResult(name, output)
    except Exception as exc:  # noqa: BLE001 - normalized into a structured failure
        return ToolResult(name, {}, normalize_failure(exc))


def _spec(name: str) -> ToolSpec:
    try:
        return CATALOG[name]
    except KeyError:
        raise invalid(name, "unknown Tool") from None


# -- shared helpers ---------------------------------------------------------------


def _config(context: ExecutionContext) -> ProjectConfig:
    config = context.project_config
    if not isinstance(config, ProjectConfig):
        raise ContractError(
            FailureCategory.INVALID_INPUT,
            "the execution context has no validated project configuration",
        )
    return config


def _settings(context: ExecutionContext) -> DjangoAngularSettings:
    if context.settings is not None:
        return cast(DjangoAngularSettings, context.settings)
    try:
        return load_angular_settings()
    except AngularCommandError as exc:
        raise ContractError(FailureCategory.INVALID_INPUT, str(exc)) from exc


def _dry(context: ExecutionContext, inputs: Mapping[str, Any]) -> bool:
    return bool(inputs.get("dry_run")) or context.dry_run


def _run(
    tool: str, argv: list[str], cwd: Path | None
) -> command_execution.CommandResult:
    """Run one command; a missing binary and a non-zero exit are told apart."""
    try:
        result = command_execution.run_command(argv, cwd=cwd, check=False)
    except command_execution.CommandExecutionError as exc:
        category = (
            FailureCategory.MISSING_DEPENDENCY
            if "not found" in str(exc)
            else FailureCategory.EXTERNAL_TOOL_FAILED
        )
        raise ContractError(
            category, f"{tool}: {exc}", {"tool": tool, "argv": argv}
        ) from exc
    except OSError as exc:
        raise ContractError(
            FailureCategory.EXTERNAL_TOOL_FAILED,
            f"{tool}: {exc}",
            {"tool": tool, "argv": argv},
        ) from exc
    if result.returncode:
        raise ContractError(
            FailureCategory.EXTERNAL_TOOL_FAILED,
            f"{tool}: '{shlex.join(argv)}' exited with {result.returncode}",
            {
                "tool": tool,
                "argv": argv,
                "returncode": result.returncode,
                "stderr": result.stderr.strip()[-_OUTPUT_TAIL:],
            },
        )
    return result


def _snapshot(root: Path) -> dict[str, tuple[int, int]]:
    """Size and mtime of every file below ``root``, without generated dependencies."""
    files: dict[str, tuple[int, int]] = {}
    if not root.is_dir():
        return files
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in _IGNORED_DIRECTORIES for part in relative.parts):
            continue
        if path.is_file():
            stat = path.stat()
            files[relative.as_posix()] = (stat.st_size, stat.st_mtime_ns)
    return files


def _delta(before: Mapping[str, Any], after: Mapping[str, Any]) -> list[str]:
    return sorted(name for name, value in after.items() if before.get(name) != value)


def _command_line(invocations: list[angular.AngularInvocation]) -> str:
    return " && ".join(shlex.join(item.argv) for item in invocations)


def _build(
    tool: str,
    builder: Callable[..., list[angular.AngularInvocation]],
    context: ExecutionContext,
    **kwargs: Any,
) -> list[angular.AngularInvocation]:
    """Resolve the invocations; the builders validate names and paths."""
    try:
        return builder(_config(context), _settings(context), **kwargs)
    except (AngularCommandError, ConfigError) as exc:
        raise invalid(tool, str(exc)) from exc


def _generate(
    tool: str,
    context: ExecutionContext,
    invocations: list[angular.AngularInvocation],
    *,
    dry_run: bool,
    root: Path | None = None,
) -> tuple[str, list[str]]:
    """Run the invocations; returns the command line and the files they changed."""
    command = _command_line(invocations)
    if dry_run:
        return command, []
    base = root or _config(context).angular_workspace
    before = _snapshot(base)
    for invocation in invocations:
        _run(tool, list(invocation.argv), invocation.cwd)
    return command, _delta(before, _snapshot(base))


def _first_source(files: list[str], within: str = "") -> str | None:
    for name in files:
        if name.endswith(".ts") and not name.endswith(".spec.ts"):
            if not within or name.startswith(within):
                return name
    return None


def _workspace_path(context: ExecutionContext, relative: str | None) -> str | None:
    if relative is None:
        return None
    return str(_config(context).angular_workspace / relative)


def _optional(inputs: Mapping[str, Any], *names: str) -> dict[str, Any]:
    return {name: inputs[name] for name in names if name in inputs}


# -- contract lifecycle -----------------------------------------------------------


def openapi_schema_export(
    context: ExecutionContext, inputs: Mapping[str, Any]
) -> Mapping[str, Any]:
    """Export the DRF schema to ``artifacts.openapiSchema``, rotating the old one."""
    from django.core.management import call_command

    from ..settings import load_drf_spectacular_settings, use_drf_spectacular_settings

    config = _config(context)
    fmt = inputs.get("format", "json")
    destination = config.openapi_schema
    previous = get_previous_schema_path(destination)
    if _dry(context, inputs):
        return {
            "destination": str(destination),
            "previous_path": str(previous) if destination.exists() else None,
            "format": fmt,
            "schema_changed": None,
        }
    try:
        spectacular_settings = load_drf_spectacular_settings()
    except ImportError as exc:
        raise ContractError(
            FailureCategory.MISSING_DEPENDENCY,
            "drf-spectacular is required for schema export",
        ) from exc
    except AngularCommandError as exc:
        raise ContractError(FailureCategory.INVALID_INPUT, str(exc)) from exc

    old = destination.read_bytes() if destination.exists() else None
    older_previous = previous.read_bytes() if previous.exists() else None

    def restore() -> None:
        if old is not None:
            destination.write_bytes(old)
        else:
            destination.unlink(missing_ok=True)
        if older_previous is not None:
            previous.write_bytes(older_previous)
        elif old is not None:
            previous.unlink(missing_ok=True)

    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        if old is not None:
            destination.replace(previous)
        with use_drf_spectacular_settings(spectacular_settings):
            call_command(
                "spectacular",
                file=str(destination),
                format="openapi" if fmt == "yaml" else "openapi-json",
            )
        data = destination.read_bytes()
        _check_schema_bytes(data, fmt)
    except ContractError:
        restore()
        raise
    except Exception as exc:  # noqa: BLE001 - the rotation is reversed first
        restore()
        raise ContractError(
            FailureCategory.EXTERNAL_TOOL_FAILED,
            f"openapi_schema_export: schema generation failed: {exc}",
            {"tool": "openapi_schema_export"},
        ) from exc
    try:
        write_record(destination, config.config_path.parent)
    except OSError as exc:
        restore()
        raise ContractError(
            FailureCategory.EXTERNAL_TOOL_FAILED,
            f"openapi_schema_export: cannot record the migrations fingerprint: {exc}",
            {"tool": "openapi_schema_export"},
        ) from exc
    return {
        "destination": str(destination),
        "previous_path": str(previous) if old is not None else None,
        "format": fmt,
        "bytes_written": len(data),
        "schema_changed": None if old is None else data != old,
    }


def _check_schema_bytes(data: bytes, fmt: str) -> None:
    text = data.decode("utf-8", errors="replace").strip()
    if not text:
        raise ContractError(
            FailureCategory.OUTPUT_INVALID, "openapi_schema_export: the schema is empty"
        )
    if fmt == "json":
        try:
            document = json.loads(text)
        except ValueError as exc:
            raise ContractError(
                FailureCategory.OUTPUT_INVALID,
                f"openapi_schema_export: the schema is not JSON: {exc}",
            ) from exc
        has_version = isinstance(document, dict) and "openapi" in document
    else:
        has_version = re.search(r"^openapi\s*:", text, re.MULTILINE) is not None
    if not has_version:
        raise ContractError(
            FailureCategory.OUTPUT_INVALID,
            "openapi_schema_export: the schema has no 'openapi' key",
        )


def validate_openapi_schema(
    context: ExecutionContext, inputs: Mapping[str, Any]
) -> Mapping[str, Any]:
    """Validate an OpenAPI artifact; a failed validation is a report, not an error."""
    tool = "validate_openapi_schema"
    path = Path(inputs["schema"])
    if not path.is_file():
        raise invalid(tool, f"schema {path} does not exist", field="schema")
    ruleset = inputs.get("ruleset", "default")
    if ruleset != "default":
        raise invalid(
            tool,
            "only the default ruleset (openapi-spec-validator) is available",
            field="ruleset",
        )
    try:
        document = load_document(path)
    except (DocumentError, OSError, UnicodeDecodeError) as exc:
        raise invalid(
            tool, f"schema {path} cannot be read: {exc}", field="schema"
        ) from exc
    errors = [
        {"code": "openapi-invalid", "message": message, "path": "", "severity": "error"}
        for message in validate_openapi_file(path)
    ]
    components = document.get("components") if isinstance(document, dict) else None
    schemas = components.get("schemas") if isinstance(components, dict) else None
    version = document.get("openapi") if isinstance(document, dict) else None
    return {
        "valid": not errors,
        "errors": errors,
        "warnings": [],
        "openapi_version": version if isinstance(version, str) else "",
        "resource_count": len(schemas) if isinstance(schemas, dict) else 0,
    }


def _oasdiff(
    tool: str, args: list[str]
) -> tuple[list[str], command_execution.CommandResult]:
    try:
        executable = tools.ensure_oasdiff()
    except tools.OasdiffUnavailableError as exc:
        raise ContractError(
            FailureCategory.MISSING_DEPENDENCY, f"{tool}: {exc}", {"tool": tool}
        ) from exc
    argv = [executable, *args]
    return argv, _run(tool, argv, None)


def _schema_pair(tool: str, inputs: Mapping[str, Any]) -> tuple[Path, Path]:
    current = Path(inputs["current_schema"])
    previous = Path(inputs["previous_schema"])
    for field, path in (("current_schema", current), ("previous_schema", previous)):
        if not path.is_file():
            raise invalid(tool, f"{field} {path} does not exist", field=field)
    return current, previous


def _json_object(tool: str, text: str) -> dict[str, Any]:
    if not text.strip():
        return {}
    try:
        document = json.loads(text)
    except ValueError as exc:
        raise ContractError(
            FailureCategory.OUTPUT_INVALID, f"{tool}: oasdiff output is not JSON: {exc}"
        ) from exc
    if not isinstance(document, dict):
        raise ContractError(
            FailureCategory.OUTPUT_INVALID, f"{tool}: oasdiff output is not an object"
        )
    return document


def _report_path(context: ExecutionContext, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else _config(context).config_path.parent / path


def _affected_resources(raw: Mapping[str, Any]) -> list[str]:
    """Resource names of the paths the diff touches (first segment that is not an
    ``api`` prefix, a version or a path parameter)."""
    paths = raw.get("paths")
    names: set[str] = set()
    if isinstance(paths, Mapping):
        entries: list[str] = []
        for key in ("added", "deleted"):
            value = paths.get(key)
            if isinstance(value, list):
                entries.extend(str(item) for item in value)
        modified = paths.get("modified")
        if isinstance(modified, Mapping):
            entries.extend(str(item) for item in modified)
        for entry in entries:
            for segment in entry.strip("/").split("/"):
                if (
                    segment
                    and segment != "api"
                    and not re.fullmatch(r"v\d+|\{.*\}", segment)
                ):
                    names.add(segment)
                    break
    return sorted(names)


def oasdiff_diff(
    context: ExecutionContext, inputs: Mapping[str, Any]
) -> Mapping[str, Any]:
    """Structured diff of two OpenAPI artifacts, with the raw report archived."""
    tool = "oasdiff_diff"
    current, previous = _schema_pair(tool, inputs)
    fmt = inputs.get("format", "json")
    report = _report_path(
        context, inputs.get("report_path", "build/oasdiff-report.json")
    )
    _, result = _oasdiff(
        tool, ["diff", str(previous), str(current), "--format", "json"]
    )
    raw = _json_object(tool, result.stdout)
    archived = result.stdout if fmt == "json" else None
    if archived is None:
        _, archive = _oasdiff(
            tool, ["diff", str(previous), str(current), "--format", fmt]
        )
        archived = archive.stdout
    try:
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(archived, encoding="utf-8")
    except OSError as exc:
        raise ContractError(
            FailureCategory.EXTERNAL_TOOL_FAILED,
            f"{tool}: cannot write {report}: {exc}",
        ) from exc
    return {
        "schema_changed": bool(raw),
        "changes": [{"section": key, "detail": raw[key]} for key in sorted(raw)],
        "affected_resources": _affected_resources(raw),
        "report_path": str(report),
    }


def oasdiff_changelog(
    context: ExecutionContext, inputs: Mapping[str, Any]
) -> Mapping[str, Any]:
    """Human-readable changelog of two OpenAPI artifacts."""
    tool = "oasdiff_changelog"
    current, previous = _schema_pair(tool, inputs)
    fmt = inputs.get("format", "markdown")
    output = _report_path(
        context, inputs.get("output_path", "build/openapi-changelog.md")
    )
    args = ["changelog", str(previous), str(current), "--format", fmt]
    command = shlex.join(["oasdiff", *args])
    if _dry(context, inputs):
        return {
            "changelog_path": str(output),
            "format": fmt,
            "schema_changed": None,
            "command": command,
        }
    _, diff = _oasdiff(tool, ["diff", str(previous), str(current), "--format", "json"])
    changed = bool(_json_object(tool, diff.stdout))
    if changed:
        argv, result = _oasdiff(tool, args)
        text = result.stdout
        command = shlex.join(argv)
        if not text.strip():
            raise ContractError(
                FailureCategory.OUTPUT_INVALID,
                f"{tool}: oasdiff produced an empty changelog for a changed schema",
            )
    else:
        text = "No changes.\n"
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    except OSError as exc:
        raise ContractError(
            FailureCategory.EXTERNAL_TOOL_FAILED,
            f"{tool}: cannot write {output}: {exc}",
        ) from exc
    return {
        "changelog_path": str(output),
        "format": fmt,
        "schema_changed": changed,
        "command": command,
    }


# -- Visual capture -------------------------------------------------------------------


def screenshot_name(url: str) -> str:
    """The file name of the capture of ``url``: host, port and path, made file-safe."""
    parts = urlsplit(url)
    raw = f"{parts.netloc}{parts.path}".strip("/")
    return re.sub(r"[^A-Za-z0-9.]+", "-", raw).strip("-") + ".png"


def _playwright_argv() -> list[str]:
    found = shutil.which("playwright")
    if found:
        return [found]
    npx = shutil.which("npx") or "npx"
    return [npx, "--no-install", "playwright"]


def demo_capture(
    context: ExecutionContext, inputs: Mapping[str, Any]
) -> Mapping[str, Any]:
    """Full-page screenshot of a running page with the Playwright command line."""
    tool = "demo_capture"
    url = str(inputs["url"])
    if urlsplit(url).scheme not in {"http", "https"} or not urlsplit(url).netloc:
        raise invalid(tool, f"url {url!r} is not an http(s) URL", field="url")
    output_dir = Path(inputs["output_dir"])
    target = output_dir / screenshot_name(url)
    argv = [*_playwright_argv(), "screenshot", "--full-page", url, str(target)]
    command = shlex.join(argv)
    if _dry(context, inputs):
        return {"screenshot_path": str(target), "url": url, "command": command}
    output_dir.mkdir(parents=True, exist_ok=True)
    target.unlink(missing_ok=True)
    _run(tool, argv, output_dir)
    if not target.is_file() or target.stat().st_size == 0:
        raise ContractError(
            FailureCategory.OUTPUT_INVALID,
            f"{tool}: the capture of {url} produced no screenshot at {target}",
            {"tool": tool, "url": url},
        )
    return {"screenshot_path": str(target), "url": url, "command": command}


# -- Angular generation wrappers ----------------------------------------------------


def _read_json(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return document if isinstance(document, dict) else {}


def angular_api_client_generate(
    context: ExecutionContext, inputs: Mapping[str, Any]
) -> Mapping[str, Any]:
    tool = "angular_api_client_generate"
    config = _config(context)
    if "schema" in inputs and Path(inputs["schema"]).resolve() != config.openapi_schema:
        raise invalid(
            tool,
            "schema must be the configured artifacts.openapiSchema",
            field="schema",
        )
    settings = _settings(context)
    generated = config.angular_workspace / "ng-openapi-gen.json"
    if _dry(context, inputs):
        # The builder writes the derived generator configuration; a dry run does not.
        argv = [
            settings.pnpm_executable,
            "exec",
            "ng-openapi-gen",
            "-c",
            str(generated),
        ]
        return {
            "output_dir": None,
            "generated_files": [],
            "client_count": 0,
            "generator_version": None,
            "command": shlex.join(argv),
        }
    invocations = _build(tool, angular.build_ng_openapi_gen_invocations, context)
    output_relative = str(_read_json(generated).get("output", ""))
    output_dir = config.angular_workspace / output_relative
    before = _snapshot(output_dir)
    for invocation in invocations:
        _run(tool, list(invocation.argv), invocation.cwd)
    files = _delta(before, _snapshot(output_dir))
    if not files:
        raise ContractError(
            FailureCategory.OUTPUT_INVALID,
            f"{tool}: ng-openapi-gen generated no files in {output_dir}",
        )
    version = _read_json(
        config.angular_workspace / "node_modules" / "ng-openapi-gen" / "package.json"
    ).get("version")
    return {
        "output_dir": str(output_dir),
        "generated_files": files,
        "client_count": sum(1 for name in files if name.endswith(".service.ts")),
        "generator_version": version if isinstance(version, str) else "unknown",
        "command": _command_line(invocations),
    }


def angular_workspace_scaffold(
    context: ExecutionContext, inputs: Mapping[str, Any]
) -> Mapping[str, Any]:
    tool = "angular_workspace_scaffold"
    config = _config(context)
    invocations = _build(
        tool,
        angular.build_ng_workspace_invocations,
        context,
        **_optional(inputs, "document"),
    )
    command, _ = _generate(tool, context, invocations, dry_run=_dry(context, inputs))
    package = _read_json(config.angular_workspace / "package.json")
    dependencies = package.get("dependencies")
    version = (
        dependencies.get("@angular/core") if isinstance(dependencies, dict) else None
    )
    return {
        "workspace_path": str(config.angular_workspace),
        "package_manager": _settings(context).package_manager,
        "angular_version": version if isinstance(version, str) else "unknown",
        "command": command,
    }


def angular_app_scaffold(
    context: ExecutionContext, inputs: Mapping[str, Any]
) -> Mapping[str, Any]:
    tool = "angular_app_scaffold"
    config = _config(context)
    invocations = _build(
        tool,
        angular.build_ng_gen_app_invocations,
        context,
        app_name=config.project_name,
        **_optional(inputs, "document", "node_id"),
    )
    command, _ = _generate(tool, context, invocations, dry_run=_dry(context, inputs))
    return {
        "app_path": str(config.angular_workspace / "projects" / config.project_name),
        "app_name": config.project_name,
        "command": command,
    }


_CLASS = re.compile(r"export\s+class\s+(\w+)")
_SELECTOR = re.compile(r"selector\s*:\s*['\"]([^'\"]+)['\"]")


def ngdj_add_component(
    context: ExecutionContext, inputs: Mapping[str, Any]
) -> Mapping[str, Any]:
    tool = "ngdj_add_component"
    require_kebab_case(tool, "name", inputs["name"])
    invocations = _build(
        tool,
        angular._COMMAND_BUILDERS["ng_component"],
        context,
        name=inputs["name"],
        target_path=inputs.get("path"),
        **_optional(inputs, "project", "document", "node_id"),
    )
    dry = _dry(context, inputs)
    command, files = _generate(tool, context, invocations, dry_run=dry)
    if dry:
        return {
            "component_path": _workspace_path(context, inputs.get("path")),
            "component_class": None,
            "selector": None,
            "generated_files": [],
            "command": command,
        }
    source = _first_source(files)
    if source is None:
        raise ContractError(
            FailureCategory.OUTPUT_INVALID,
            f"{tool}: generation produced no component source",
        )
    text = (_config(context).angular_workspace / source).read_text(encoding="utf-8")
    class_match, selector_match = _CLASS.search(text), _SELECTOR.search(text)
    if class_match is None or selector_match is None:
        raise ContractError(
            FailureCategory.OUTPUT_INVALID,
            f"{tool}: {source} declares no component class and selector",
        )
    return {
        "component_path": str(_config(context).angular_workspace / source),
        "component_class": class_match.group(1),
        "selector": selector_match.group(1),
        "generated_files": files,
        "command": command,
    }


def ngdj_add_page(
    context: ExecutionContext, inputs: Mapping[str, Any]
) -> Mapping[str, Any]:
    tool = "ngdj_add_page"
    invocations = _build(
        tool,
        angular._COMMAND_BUILDERS["ng_page"],
        context,
        name=inputs["name"],
        target_path=inputs["path"],
        **_optional(
            inputs,
            "project",
            "route_path",
            "access",
            "auth_guard",
            "navigation_label",
            "navigation_icon",
            "document",
            "node_id",
        ),
    )
    command, files = _generate(
        tool, context, invocations, dry_run=_dry(context, inputs)
    )
    return {
        "page_path": _workspace_path(context, inputs["path"]),
        "generated_files": files,
        "command": command,
    }


def ngdj_add_reactive_form(
    context: ExecutionContext, inputs: Mapping[str, Any]
) -> Mapping[str, Any]:
    tool = "ngdj_add_reactive_form"
    invocations = _build(
        tool,
        angular._COMMAND_BUILDERS["ng_reactive_form"],
        context,
        name=inputs["name"],
        target_path=inputs.get("path"),
        **_optional(
            inputs, "document", "node_id", "definition", "project", "primitives_path"
        ),
    )
    command, files = _generate(
        tool, context, invocations, dry_run=_dry(context, inputs)
    )
    source = _first_source(files)
    return {
        "form_path": (
            _workspace_path(context, source)
            if source
            else _workspace_path(context, inputs.get("path"))
        ),
        "generated_files": files,
        "command": command,
    }


def ngdj_add_complex_component(
    context: ExecutionContext, inputs: Mapping[str, Any]
) -> Mapping[str, Any]:
    tool = "ngdj_add_complex_component"
    invocations = _build(
        tool,
        angular._COMMAND_BUILDERS["ng_complex_component"],
        context,
        name=inputs["name"],
        target_path=inputs["path"],
        features=inputs["features"],
        **_optional(inputs, "mode", "confirm", "project", "document", "node_id"),
    )
    command, files = _generate(
        tool, context, invocations, dry_run=_dry(context, inputs)
    )
    return {
        "component_path": _workspace_path(context, inputs["path"]),
        "generated_files": files,
        "command": command,
    }


def ngdj_add_data_service(
    context: ExecutionContext, inputs: Mapping[str, Any]
) -> Mapping[str, Any]:
    tool = "ngdj_add_data_service"
    invocations = _build(
        tool,
        angular._COMMAND_BUILDERS["ng_data_service"],
        context,
        resource=inputs["resource"],
        **_optional(inputs, "project", "path", "api_service"),
    )
    command, files = _generate(
        tool, context, invocations, dry_run=_dry(context, inputs)
    )
    source = _first_source(files)
    return {
        "service_path": (
            _workspace_path(context, source)
            if source
            else _workspace_path(context, inputs.get("path"))
        ),
        "generated_files": files,
        "command": command,
    }


def _widget(tool: str, schematic: str):
    def run(context: ExecutionContext, inputs: Mapping[str, Any]) -> Mapping[str, Any]:
        mapping = _mapping(tool, context)
        node_id = inputs.get("node_id") or _first_node_id(
            tool, context, inputs["document"], mapping, schematic
        )
        invocations = _build(
            tool,
            angular.build_ngdj_schematic_invocations,
            context,
            schematic=schematic,
            document=inputs["document"],
            node_id=node_id,
            **_optional(inputs, "name", "path", "project"),
        )
        command, files = _generate(
            tool, context, invocations, dry_run=_dry(context, inputs)
        )
        return {"generated_files": files, "command": command}

    run.__name__ = tool
    return run


ngdj_add_tabs = _widget("ngdj_add_tabs", "tabs")
ngdj_add_dialog = _widget("ngdj_add_dialog", "dialog")
ngdj_add_stepper = _widget("ngdj_add_stepper", "stepper")
ngdj_add_table = _widget("ngdj_add_table", "table")


def _mapping(tool: str, context: ExecutionContext) -> CommandMapping:
    config = _config(context)
    try:
        return load_command_mapping(
            config.angular_workspace, _settings(context).ng_add_package
        )
    except CommandMappingError as exc:
        category = (
            FailureCategory.MISSING_DEPENDENCY
            if "not found" in str(exc)
            else FailureCategory.INVALID_INPUT
        )
        raise ContractError(category, f"{tool}: {exc}", {"tool": tool}) from exc


def _first_node_id(
    tool: str,
    context: ExecutionContext,
    document_path: str,
    mapping: CommandMapping,
    schematic: str,
) -> str:
    """The id of the first element the ngdj command compiles, in document order."""
    config = _config(context)
    path = Path(document_path)
    if not path.is_absolute():
        path = config.angular_workspace / path
    try:
        document = load_document(path)
    except (DocumentError, OSError) as exc:
        raise invalid(
            tool, f"document {path} cannot be read: {exc}", field="document"
        ) from exc
    node_types = {
        node_type
        for node_type in mapping.node_types()
        if any(c.command == schematic for c in mapping.commands_for(node_type))
    }

    def walk(node: Any) -> str | None:
        if isinstance(node, Mapping):
            if node.get("type") in node_types and isinstance(node.get("id"), str):
                return str(node["id"])
            for child in node.get("children", ()) or ():
                found = walk(child)
                if found:
                    return found
        return None

    found = walk(document)
    if found is None:
        raise invalid(
            tool, f"{path} has no element compiled by {schematic}", field="document"
        )
    return found


# -- ngdj_run_schematic -------------------------------------------------------------


def ngdj_run_schematic(
    context: ExecutionContext, inputs: Mapping[str, Any]
) -> Mapping[str, Any]:
    """Run one schematic of the ngdj mapping; options are validated, not passed."""
    tool = "ngdj_run_schematic"
    name = str(inputs["schematic"]).removeprefix(_SCHEMATIC_PREFIX)
    if ":" in name or not re.fullmatch(r"[a-z][a-z0-9-]*", name):
        raise invalid(
            tool, "arbitrary collection names are not accepted", field="schematic"
        )
    mapping = _mapping(tool, context)
    try:
        parameters = {
            entry["name"]: entry
            for entry in mapping._command(name).get("parameters", ())
        }
    except CommandMappingError as exc:
        raise invalid(
            tool, f"{name} is not a schematic of the command mapping", field="schematic"
        ) from exc
    options = dict(inputs.get("options", {}))
    if "project" in inputs:
        options.setdefault("project", inputs["project"])
    argv = [_settings(context).ng_executable, "generate", f"{_SCHEMATIC_PREFIX}{name}"]
    positional: dict[int, str] = {}
    flags: list[str] = []
    for key in sorted(options):
        parameter = parameters.get(_camel(key))
        if parameter is None:
            raise invalid(tool, f"{name} has no option '{key}'", field=f"options.{key}")
        value = _check_option(tool, parameter, key, options[key])
        if "positional" in parameter:
            positional[int(parameter["positional"])] = str(value)
        elif parameter.get("type") == "boolean":
            flags.append(f"{parameter['flag']}={'true' if value else 'false'}")
        else:
            flags.append(f"{parameter['flag']}={value}")
    argv.extend(positional[index] for index in sorted(positional))
    argv.extend(flags)
    command = shlex.join(argv)
    if _dry(context, inputs):
        return {
            "schematic": f"{_SCHEMATIC_PREFIX}{name}",
            "generated_files": [],
            "command": command,
            "warnings": [],
        }
    config = _config(context)
    before = _snapshot(config.angular_workspace)
    result = _run(tool, argv, config.angular_workspace)
    warnings = [
        line.strip()
        for line in (result.stdout + "\n" + result.stderr).splitlines()
        if "warn" in line.lower()
    ]
    return {
        "schematic": f"{_SCHEMATIC_PREFIX}{name}",
        "generated_files": _delta(before, _snapshot(config.angular_workspace)),
        "command": command,
        "warnings": warnings,
    }


def _camel(key: str) -> str:
    head, *rest = key.split("_")
    return head + "".join(part.title() for part in rest)


def _check_option(tool: str, parameter: Mapping[str, Any], key: str, value: Any) -> Any:
    kind = parameter.get("type", "string")
    field = f"options.{key}"
    if kind == "boolean":
        if not isinstance(value, bool):
            raise invalid(tool, f"option '{key}' must be a boolean", field=field)
    elif kind == "string":
        if not isinstance(value, str) or not value:
            raise invalid(
                tool, f"option '{key}' must be a non-empty string", field=field
            )
        if "\n" in value:
            raise invalid(tool, f"option '{key}' must be a single line", field=field)
    elif not isinstance(value, (str, int, float)) or isinstance(value, bool):
        raise invalid(tool, f"option '{key}' has an unsupported value", field=field)
    allowed = parameter.get("enum")
    if allowed is not None and value not in allowed:
        raise invalid(tool, f"option '{key}' must be one of {allowed}", field=field)
    return value


# -- ngdj_add_feature -----------------------------------------------------------------

_ROUTES: Final = re.compile(r"export\s+const\s+routes\s*(?::\s*Routes\s*)?=\s*\[")


def ngdj_add_feature(
    context: ExecutionContext, inputs: Mapping[str, Any]
) -> Mapping[str, Any]:
    """A feature area: a page component, a route file and its registration."""
    tool = "ngdj_add_feature"
    config = _config(context)
    name = inputs["name"]
    page_name = inputs.get("page_name", name)
    route_path = inputs.get("route_path", name)
    parent = inputs.get("path", "src/app/features")
    for field, value in (("name", name), ("page_name", page_name)):
        require_kebab_case(tool, field, value)
    if not re.fullmatch(r"[A-Za-z0-9._~-]+", route_path):
        raise invalid(tool, f"invalid route_path {route_path!r}", field="route_path")
    parts = Path(parent).parts
    if Path(parent).is_absolute() or ".." in parts or not parent.startswith("src/app"):
        raise invalid(
            tool, "path must lie inside the application source root", field="path"
        )
    feature = config.angular_workspace / parent / name
    if feature.exists():
        raise invalid(tool, f"the feature area {feature} already exists", field="name")
    app_routes = config.angular_workspace / "src" / "app" / "app.routes.ts"
    register = inputs.get("register_route", True)
    if register and not app_routes.is_file():
        raise invalid(
            tool,
            "route registration needs an application route tree "
            "(src/app/app.routes.ts)",
            field="register_route",
        )
    export = _routes_export(name)
    invocations = _build(
        tool,
        angular._COMMAND_BUILDERS["ng_component"],
        context,
        name=page_name,
        target_path=f"{parent}/{name}/{page_name}",
        **_optional(inputs, "project"),
    )
    commands = [shlex.join(item.argv) for item in invocations]
    routes_file = feature / f"{name}.routes.ts"
    result: dict[str, Any] = {
        "feature_path": str(feature),
        "page_component_path": None,
        "feature_routes_path": str(routes_file),
        "app_routes_path": str(app_routes) if register else None,
        "generated_files": [],
        "commands": commands,
    }
    if _dry(context, inputs):
        return result
    before = _snapshot(feature)
    for invocation in invocations:
        _run(tool, list(invocation.argv), invocation.cwd)
    files = _delta(before, _snapshot(feature))
    source = _first_source(files)
    if source is None:
        raise ContractError(
            FailureCategory.OUTPUT_INVALID,
            f"{tool}: generation produced no page component",
        )
    page_file = feature / source
    match = _CLASS.search(page_file.read_text(encoding="utf-8"))
    if match is None:
        raise ContractError(
            FailureCategory.OUTPUT_INVALID, f"{tool}: {source} declares no class"
        )
    import_path = "./" + Path(source).with_suffix("").as_posix()
    routes_file.write_text(
        "import { Routes } from '@angular/router';\n\n"
        f"export const {export}: Routes = [\n"
        f"  {{ path: '', loadComponent: () => import('{import_path}')"
        f".then((m) => m.{match.group(1)}) }},\n"
        "];\n",
        encoding="utf-8",
        newline="\n",
    )
    if not routes_file.is_file():
        raise ContractError(
            FailureCategory.OUTPUT_INVALID,
            f"{tool}: the feature route definition was not written",
        )
    if register:
        entry = (
            f"  {{ path: '{route_path}', loadChildren: () => "
            f"import('./{parent.removeprefix('src/app/')}/{name}/{name}.routes')"
            f".then((m) => m.{export}) }},\n"
        )
        _register_route(tool, app_routes, entry)
    generated = sorted({*files, routes_file.relative_to(feature).as_posix()})
    result.update(
        page_component_path=str(page_file),
        generated_files=generated,
    )
    return result


def _routes_export(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", name).upper() + "_ROUTES"


def _register_route(tool: str, app_routes: Path, entry: str) -> None:
    """Insert ``entry`` before the closing bracket of the ``routes`` array."""
    text = app_routes.read_text(encoding="utf-8")
    opening = _ROUTES.search(text)
    if opening is None:
        raise invalid(tool, f"{app_routes} declares no `routes` array")
    closing = _matching_bracket(text, opening.end() - 1)
    if closing is None:
        raise invalid(tool, f"the `routes` array of {app_routes} is not closed")
    prefix = text[:closing]
    if not prefix.rstrip().endswith((",", "[")):
        prefix = prefix.rstrip() + ",\n"
    elif not prefix.endswith("\n"):
        prefix += "\n"
    app_routes.write_text(
        prefix + entry + text[closing:], encoding="utf-8", newline="\n"
    )


def _matching_bracket(text: str, start: int) -> int | None:
    """Index of the ``]`` closing the ``[`` at ``start`` (strings, comments skipped)."""
    depth = 0
    index = start
    quote = ""
    while index < len(text):
        char = text[index]
        if quote:
            if char == "\\":
                index += 1
            elif char == quote:
                quote = ""
        elif text.startswith("//", index):
            index = text.find("\n", index)
            if index < 0:
                return None
        elif text.startswith("/*", index):
            index = text.find("*/", index)
            if index < 0:
                return None
            index += 1
        elif char in "'\"`":
            quote = char
        elif char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return None
