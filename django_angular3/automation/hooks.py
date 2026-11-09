"""Provider-neutral lifecycle Hooks and their registry (``HOOK_CONTRACTS.md``).

The registry is keyed by the canonical Hook name and the lifecycle family
(``pre-tool``, ``post-tool``, ``session-stop``). Matching uses canonical identities
only: the Hook name, the family and the canonical Tool (or external command) name. It
never inspects a raw shell string or a provider-native event name; adapters and the
direct controller first normalize an observation (``observation_from_provider``,
``command_identity``) to that identity, and a duplicate observation is idempotent.

Each Hook performs its deterministic action by invoking Tool contracts by name
(``invoke_tool``), never the underlying binary. Failures are ``ContractError`` with
the category ``hook_failed``; the consequence (block, halt, warn) follows the family
and is applied by ``DirectExecutor``. Durable artifacts below the build output:
``hook-log.jsonl``, ``verification.log``, ``session-log.json`` and ``history/``.
No provider SDK is imported here.
"""

from __future__ import annotations

import json
import shlex
import shutil
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final, TextIO

from .. import command_execution
from .contracts import (
    ContractError,
    FailureCategory,
    HookFamily,
    HookOutcome,
    dumps,
)
from .execution import (
    ExecutionContext,
    HookBinding,
    HookObservation,
    normalize_failure,
)
from .migrations import (
    migration_modules,
    migrations_fingerprint,
    read_record,
)
from .tools import invoke_tool

HOOK_LOG: Final = "hook-log.jsonl"
VERIFICATION_LOG: Final = "verification.log"
SESSION_LOG: Final = "session-log.json"
SESSION_TIMESTAMP: Final = "session-timestamp.txt"
HISTORY: Final = "history"

GENERATION_TOOLS: Final = frozenset(
    {
        "angular_api_client_generate",
        "angular_workspace_scaffold",
        "angular_app_scaffold",
    }
)
#: The canonical identity of a ``makemigrations`` run (an external command, not a Tool).
MAKEMIGRATIONS: Final = "makemigrations"

PRE_CONSTRUCTION: Final = "pre-construction"
MIGRATION_TRIGGERED: Final = "migration-triggered"
POST_GENERATION: Final = "post-generation"
DEMO_CAPTURE: Final = "demo-capture"
DEMO_DIRECTORY: Final = "demo"
SESSION_STOP: Final = "session-stop"

Clock = Callable[[], str]


def utc_timestamp() -> str:
    """``YYYYMMDDTHHMMSSZ`` of now; the default clock at the execution boundary."""
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


# -- registry ---------------------------------------------------------------------


@dataclass(frozen=True)
class HookRegistration:
    """A catalogued Hook: canonical identity, scope and implementation."""

    name: str
    family: HookFamily
    function: Callable[[ExecutionContext, HookObservation], None]
    #: Canonical Tool or external command names the Hook wraps; ``None`` for
    #: ``session-stop``, which is not scoped to a Tool.
    tools: frozenset[str] | None = None

    def binding(self) -> HookBinding:
        return HookBinding(self.name, self.family, self.function, self.tools)


@dataclass
class HookRegistry:
    """Hooks keyed by canonical name and lifecycle family."""

    _registrations: dict[tuple[str, HookFamily], HookRegistration] = field(
        default_factory=dict
    )
    _seen: dict[tuple[str, str], HookOutcome] = field(default_factory=dict)

    def register(self, registration: HookRegistration) -> None:
        key = (registration.name, registration.family)
        if key in self._registrations:
            raise ContractError(
                FailureCategory.INVALID_INPUT,
                f"hook {registration.name} is already registered for "
                f"{registration.family.value}",
            )
        self._registrations[key] = registration

    def registrations(self) -> tuple[HookRegistration, ...]:
        return tuple(self._registrations.values())

    def bindings(self) -> list[HookBinding]:
        """The Hooks as ``DirectExecutor`` bindings, in registration order."""
        return [r.binding() for r in self._registrations.values()]

    def select(self, family: HookFamily, tool: str | None) -> list[HookRegistration]:
        """The Hooks of ``family`` that wrap ``tool`` (canonical identity only)."""
        return [
            r
            for r in self._registrations.values()
            if r.family is family
            and (
                family is HookFamily.SESSION_STOP or r.tools is None or tool in r.tools
            )
        ]

    def dispatch(
        self,
        context: ExecutionContext,
        observation: HookObservation,
        observation_id: str | None = None,
    ) -> tuple[HookOutcome, ...]:
        """Run the matching Hooks for one observation.

        A repeated ``observation_id`` returns the earlier outcomes without running
        the Hooks again, so a duplicate lifecycle observation never repeats
        destructive work (an archive) or emits conflicting evidence.
        """
        outcomes: list[HookOutcome] = []
        for registration in self.select(observation.family, observation.tool):
            key = (registration.name, observation_id or "")
            if observation_id is not None and key in self._seen:
                outcomes.append(self._seen[key])
                continue
            try:
                registration.function(context, observation)
                outcome = HookOutcome(registration.name, registration.family)
            except Exception as exc:  # noqa: BLE001 - normalized, never raw
                failure = normalize_failure(exc, hook_name=registration.name)
                outcome = HookOutcome(registration.name, registration.family, failure)
            if observation_id is not None:
                self._seen[key] = outcome
            outcomes.append(outcome)
        return tuple(outcomes)


# -- observations of providers and commands ---------------------------------------

_PROVIDER_EVENTS: Final[Mapping[str, Mapping[str, HookFamily]]] = {
    "claude": {
        "PreToolUse": HookFamily.PRE_TOOL,
        "PostToolUse": HookFamily.POST_TOOL,
        "Stop": HookFamily.SESSION_STOP,
    },
    "copilot": {
        "on_pre_tool_use": HookFamily.PRE_TOOL,
        "on_post_tool_use": HookFamily.POST_TOOL,
    },
}
_SHELL_TOOLS: Final = frozenset({"Bash", "bash", "shell", "run_shell_command"})


def command_identity(argv: Sequence[str]) -> str | None:
    """The canonical identity of a command line, from its tokens.

    ``manage.py makemigrations ...`` and ``django-admin makemigrations ...`` are the
    ``makemigrations`` command; a ``makemigrations`` substring elsewhere (an argument
    of another command, a path) is not.
    """
    tokens = list(argv)
    for index, token in enumerate(tokens):
        if Path(token).name in {"manage.py", "django-admin", "django-admin.py"}:
            rest = [t for t in tokens[index + 1 :] if not t.startswith("-")]
            return MAKEMIGRATIONS if rest[:1] == [MAKEMIGRATIONS] else None
    return None


def observation_from_provider(
    provider: str, event: str, payload: Mapping[str, Any]
) -> tuple[HookObservation, str | None]:
    """Normalize a provider-shaped lifecycle observation to a registry identity.

    Returns the observation (family and canonical Tool or command identity) and the
    provider's identifier of the call, used to make a duplicate observation idempotent.
    """
    try:
        family = _PROVIDER_EVENTS[provider][event]
    except KeyError:
        raise ContractError(
            FailureCategory.INVALID_INPUT,
            f"unknown lifecycle event {event!r} of provider {provider!r}",
        ) from None
    if family is HookFamily.SESSION_STOP:
        return HookObservation(family, None, {}), _call_id(payload)
    name = payload.get("tool_name", payload.get("toolName"))
    arguments = payload.get("tool_input", payload.get("toolArgs")) or {}
    if not isinstance(name, str) or not name or not isinstance(arguments, Mapping):
        raise ContractError(
            FailureCategory.INVALID_INPUT, "the observation names no Tool"
        )
    tool = name.rsplit("__", 1)[-1]
    if tool in _SHELL_TOOLS and isinstance(arguments.get("command"), str):
        try:
            identity = command_identity(shlex.split(arguments["command"]))
        except ValueError:
            identity = None
        tool = identity or tool
    return HookObservation(family, tool, dict(arguments)), _call_id(payload)


def _call_id(payload: Mapping[str, Any]) -> str | None:
    value = payload.get("tool_use_id", payload.get("toolCallId"))
    return value if isinstance(value, str) else None


# -- artifacts ----------------------------------------------------------------------


def _append_line(path: Path, record: Mapping[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(dumps(record) + "\n")
    except OSError as exc:
        raise ContractError(
            FailureCategory.HOOK_FAILED,
            f"cannot write {path}: {exc}",
            {"path": str(path)},
        ) from exc


def _fail(
    hook: str,
    context: ExecutionContext,
    stderr: TextIO | None,
    message: str,
    **details: Any,
) -> ContractError:
    """Record a Hook failure to stderr and the Hook log; returns the error to raise."""
    record = {"hook": hook, "category": FailureCategory.HOOK_FAILED.value}
    record.update(message=message, **details)
    stream = stderr if stderr is not None else sys.stderr
    print(dumps(record), file=stream)
    try:
        _append_line(context.output_dir / HOOK_LOG, record)
    except ContractError:
        pass  # the stderr record stands; the original failure is what matters
    return ContractError(
        FailureCategory.HOOK_FAILED, message, {"hook": hook, **details}
    )


def _log(context: ExecutionContext, record: Mapping[str, Any]) -> None:
    _append_line(context.output_dir / HOOK_LOG, record)


def _project_root(context: ExecutionContext) -> Path:
    return Path(context.project_config.config_path).parent


def _migration_files(root: Path) -> dict[str, tuple[int, int]]:
    """Size and mtime of every migration module below ``root``."""
    files: dict[str, tuple[int, int]] = {}
    for path in migration_modules(root):
        stat = path.stat()
        files[path.relative_to(root).as_posix()] = (stat.st_size, stat.st_mtime_ns)
    return files


def snapshot_migrations(context: ExecutionContext) -> dict[str, tuple[int, int]]:
    """The pre-call snapshot the ``migration-triggered`` Hook compares against."""
    return _migration_files(_project_root(context))


# -- the catalogued Hooks ------------------------------------------------------------


def pre_construction_hook(
    stderr: TextIO | None = None,
) -> Callable[[ExecutionContext, HookObservation], None]:
    """Block generation unless the schema exists, is fresh and validates."""

    def run(context: ExecutionContext, observation: HookObservation) -> None:
        schema = context.project_config.openapi_schema
        if not schema.is_file():
            raise _fail(
                PRE_CONSTRUCTION,
                context,
                stderr,
                f"the schema {schema} does not exist",
                reason="missing",
                schema_path=str(schema),
            )
        recorded = read_record(schema)
        if recorded is not None and recorded != migrations_fingerprint(
            _project_root(context)
        ):
            raise _fail(
                PRE_CONSTRUCTION,
                context,
                stderr,
                f"the schema {schema} was exported against other migrations",
                reason="stale",
                schema_path=str(schema),
            )
        result = invoke_tool(
            "validate_openapi_schema", {"schema": str(schema)}, context
        )
        if not result.ok:
            raise _fail(
                PRE_CONSTRUCTION,
                context,
                stderr,
                f"validate_openapi_schema failed: "
                f"{result.failure.message if result.failure else ''}",
                reason="tool_failed",
                schema_path=str(schema),
            )
        if not result.output.get("valid"):
            raise _fail(
                PRE_CONSTRUCTION,
                context,
                stderr,
                f"the schema {schema} is not valid OpenAPI",
                reason="invalid",
                schema_path=str(schema),
                errors=[e.get("message") for e in result.output.get("errors", ())],
            )
        _log(
            context,
            {"hook": PRE_CONSTRUCTION, "pass": True, "schema_path": str(schema)},
        )

    return run


def migration_triggered_hook(
    stderr: TextIO | None = None,
) -> Callable[[ExecutionContext, HookObservation], None]:
    """Re-export the schema when a ``makemigrations`` run added or changed migrations.

    The observation's inputs carry ``migrations_before``, the snapshot from
    ``snapshot_migrations`` taken before the call. A failed export halts and does not
    roll back the migration.
    """

    def run(context: ExecutionContext, observation: HookObservation) -> None:
        before = observation.inputs.get("migrations_before", {})
        after = snapshot_migrations(context)
        changed = sorted(
            name for name, value in after.items() if before.get(name) != value
        )
        if not changed:
            return
        result = invoke_tool("openapi_schema_export", {}, context)
        if not result.ok:
            failure = result.failure
            raise _fail(
                MIGRATION_TRIGGERED,
                context,
                stderr,
                f"openapi_schema_export failed: {failure.message if failure else ''}",
                details=dict(failure.details) if failure else {},
                migrations=changed,
            )
        _log(
            context,
            {
                "hook": MIGRATION_TRIGGERED,
                "migrations": changed,
                "destination": result.output.get("destination"),
                "previous_path": result.output.get("previous_path"),
                "schema_changed": result.output.get("schema_changed"),
            },
        )

    return run


def post_generation_hook(
    clock: Clock = utc_timestamp,
    stderr: TextIO | None = None,
    client_check: str = "tsc",
) -> Callable[[ExecutionContext, HookObservation], None]:
    """Check the structure a generation Tool left and log the result; never repairs.

    ``client_check`` selects the check after ``angular_api_client_generate``: ``tsc``
    (the contract: ``tsc --noEmit`` in the workspace) or ``structure`` (the generated
    client files exist). ``build_app`` uses ``structure``: in the middle of a build the
    application cannot compile yet, and compilation is checked once by the terminal
    validation (``ng_build``).
    """
    if client_check not in {"tsc", "structure"}:
        raise ValueError(f"unknown client_check {client_check!r}")

    def run(context: ExecutionContext, observation: HookObservation) -> None:
        tool = observation.tool or ""
        output = observation.result.output if observation.result else {}
        generated = list(output.get("generated_files", ()))
        passed, details = _structural_check(tool, context, output, client_check)
        _append_line(
            context.output_dir / VERIFICATION_LOG,
            {
                "hook": POST_GENERATION,
                "tool": tool,
                "pass": passed,
                "details": details,
                "generated_files": generated,
                "timestamp": clock(),
            },
        )
        if not passed:
            raise _fail(
                POST_GENERATION,
                context,
                stderr,
                f"the structural check of {tool} failed: {details}",
                tool=tool,
            )

    return run


def _client_structure(workspace: Path) -> tuple[bool, str]:
    """The generated client exists: services below the output of ``ng-openapi-gen``."""
    try:
        generated = json.loads(
            (workspace / "ng-openapi-gen.json").read_text(encoding="utf-8")
        )
        output = workspace / str(generated["output"])
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return False, f"the ng-openapi-gen configuration cannot be read: {exc}"
    services = sorted(output.rglob("*.service.ts")) if output.is_dir() else []
    if not services:
        return False, f"no generated client service below {output}"
    return True, f"{len(services)} generated client service file(s) below {output}"


def _structural_check(
    tool: str,
    context: ExecutionContext,
    output: Mapping[str, Any],
    client_check: str = "tsc",
) -> tuple[bool, str]:
    config = context.project_config
    workspace: Path = config.angular_workspace
    if tool == "angular_api_client_generate" and client_check == "structure":
        return _client_structure(workspace)
    if tool == "angular_api_client_generate":
        settings = context.settings
        if settings is None:
            from ..settings import load_angular_settings

            settings = load_angular_settings()
        argv = [settings.pnpm_executable, "exec", "tsc", "--noEmit"]
        try:
            result = command_execution.run_command(argv, cwd=workspace, check=False)
        except (command_execution.CommandExecutionError, OSError) as exc:
            return False, f"tsc --noEmit could not run: {exc}"
        if result.returncode:
            tail = (result.stdout + result.stderr).strip()[-500:]
            return False, f"tsc --noEmit exited with {result.returncode}: {tail}"
        return True, "tsc --noEmit passed"
    if tool == "angular_workspace_scaffold":
        expected = [workspace / "angular.json", workspace / "package.json"]
    elif tool == "angular_app_scaffold":
        expected = [workspace / "projects" / config.project_name / "src"]
    else:
        return False, f"no structural check is defined for {tool!r}"
    missing = [str(path) for path in expected if not path.exists()]
    if missing:
        return False, f"missing: {', '.join(missing)}"
    return True, "expected workspace files are present"


def session_stop_hook(
    clock: Clock = utc_timestamp, stderr: TextIO | None = None
) -> Callable[[ExecutionContext, HookObservation], None]:
    """Archive the run's artifacts and record the session summary; idempotent."""

    def run(context: ExecutionContext, observation: HookObservation) -> None:
        build = context.output_dir
        stamp = _session_timestamp(build, clock)
        history = build / HISTORY / stamp
        summary = {
            "hook": SESSION_STOP,
            "timestamp": stamp,
            "schema_version": _schema_version(),
            **{
                key: observation.summary.get(key)
                for key in (
                    "commands_completed",
                    "commands_failed",
                    "hook_failures",
                    "exit_code",
                )
            },
        }
        problem: str | None = None
        try:
            for source in _archive_sources(build):
                history.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(history / source.name))
        except OSError as exc:
            problem = f"archiving failed: {exc}"
        try:
            _record_session(build / SESSION_LOG, summary)
        except OSError as exc:
            problem = problem or f"the session log is not writable: {exc}"
        if problem:
            record = {
                "hook": SESSION_STOP,
                "category": FailureCategory.HOOK_FAILED.value,
                "message": problem,
                "details": {"timestamp": stamp},
            }
            print(dumps(record), file=stderr if stderr is not None else sys.stderr)
            raise ContractError(
                FailureCategory.HOOK_FAILED, problem, {"hook": SESSION_STOP}
            )

    return run


def _session_timestamp(build: Path, clock: Clock) -> str:
    path = build / SESSION_TIMESTAMP
    try:
        if path.is_file():
            text = path.read_text(encoding="utf-8").strip()
            if text:
                return text
        stamp = clock()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(stamp + "\n", encoding="utf-8")
        return stamp
    except OSError as exc:
        raise ContractError(
            FailureCategory.HOOK_FAILED, f"cannot persist the session timestamp: {exc}"
        ) from exc


def _archive_sources(build: Path) -> list[Path]:
    names = [VERIFICATION_LOG, HOOK_LOG, "oasdiff-report.json"]
    sources = sorted(build.glob("command-execution.*"))
    sources.extend(build / name for name in names if (build / name).exists())
    return sources


def _record_session(path: Path, summary: Mapping[str, Any]) -> None:
    entries: list[Any] = []
    if path.is_file():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            loaded = []
        entries = loaded if isinstance(loaded, list) else []
    if any(
        isinstance(e, dict) and e.get("timestamp") == summary["timestamp"]
        for e in entries
    ):
        return
    entries.append(dict(summary))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(entries, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _schema_version() -> str | None:
    from ..ngdj_command_mapping import (
        CommandMappingError,
        installed_openui_schema_version,
    )

    try:
        return installed_openui_schema_version()
    except CommandMappingError:
        return None


# -- the default registry --------------------------------------------------------------


# -- demo-capture ------------------------------------------------------------------


@dataclass(frozen=True)
class DemoTarget:
    """One row of the registry (``DEMO.md``): a page and its reproduction steps."""

    name: str
    url: str
    server_command: str
    fixture_setup: str
    actions: str

    def empty_fields(self) -> list[str]:
        return [
            label
            for label, value in (
                ("Target", self.name),
                ("URL", self.url),
                ("Server command", self.server_command),
                ("Fixture setup", self.fixture_setup),
                ("Actions", self.actions),
            )
            if not value.strip()
        ]


def demo_targets(demo_file: Path) -> list[DemoTarget]:
    """The registered targets: the rows of the table in ``demo_file``."""
    targets: list[DemoTarget] = []
    for line in demo_file.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if len(cells) != 5 or set(cells[0]) <= {"-", ":", " "} or cells[0] == "Target":
            continue
        targets.append(DemoTarget(*cells))
    return targets


def demo_capture_hook(
    demo_file: Path,
    clock: Clock = utc_timestamp,
    stderr: TextIO | None = None,
) -> Callable[[ExecutionContext, HookObservation], None]:
    """Capture every registered target and check its reproduction entry; never repairs.

    The application must already run at each URL (the end-to-end flow boots it). One
    entry per target goes to ``verification.log``; a failed capture or an incomplete
    entry halts after all targets were tried. A visual difference is never a failure.
    """

    def run(context: ExecutionContext, observation: HookObservation) -> None:
        tool = observation.tool or ""
        try:
            targets = demo_targets(demo_file)
        except OSError as exc:
            raise _fail(
                DEMO_CAPTURE, context, stderr, f"{demo_file} cannot be read: {exc}"
            ) from exc
        log = context.output_dir / VERIFICATION_LOG
        failed: list[str] = []
        if not targets:
            _append_line(
                log,
                {
                    "hook": DEMO_CAPTURE,
                    "tool": tool,
                    "target": None,
                    "pass": True,
                    "details": "no registered target",
                    "timestamp": clock(),
                },
            )
        for target in targets:
            passed, details, screenshot = True, "captured", None
            if missing := target.empty_fields():
                passed, details = (
                    False,
                    f"the DEMO.md entry has no {', '.join(missing)}",
                )
            else:
                result = invoke_tool(
                    "demo_capture",
                    {
                        "url": target.url,
                        "output_dir": str(context.output_dir / DEMO_DIRECTORY),
                    },
                    context,
                )
                if result.failure is not None:
                    passed, details = False, result.failure.message
                else:
                    screenshot = result.output["screenshot_path"]
            if not passed:
                failed.append(target.name)
            _append_line(
                log,
                {
                    "hook": DEMO_CAPTURE,
                    "tool": tool,
                    "target": target.name,
                    "url": target.url,
                    "pass": passed,
                    "details": details,
                    "screenshot_path": screenshot,
                    "timestamp": clock(),
                },
            )
        if failed:
            raise _fail(
                DEMO_CAPTURE,
                context,
                stderr,
                f"the capture of {', '.join(failed)} failed; see {VERIFICATION_LOG}",
                tool=tool,
            )

    return run


def demo_capture_registration(
    demo_file: Path,
    tools: frozenset[str],
    clock: Clock = utc_timestamp,
    stderr: TextIO | None = None,
) -> HookRegistration:
    """``demo-capture`` as a ``post-tool`` Hook scoped to ``tools``.

    Register it after ``post-generation`` so that it runs only when that check passed.
    """
    return HookRegistration(
        DEMO_CAPTURE,
        HookFamily.POST_TOOL,
        demo_capture_hook(demo_file, clock, stderr),
        tools,
    )


def default_registry(
    clock: Clock = utc_timestamp,
    stderr: TextIO | None = None,
    client_check: str = "structure",
) -> HookRegistry:
    """The four catalogued Hooks, registered under their canonical names.

    ``client_check`` is the ``post-generation`` check after the client generation (see
    ``post_generation_hook``); the default is the structure check that fits the middle
    of a build.
    """
    registry = HookRegistry()
    registry.register(
        HookRegistration(
            PRE_CONSTRUCTION,
            HookFamily.PRE_TOOL,
            pre_construction_hook(stderr),
            GENERATION_TOOLS,
        )
    )
    registry.register(
        HookRegistration(
            MIGRATION_TRIGGERED,
            HookFamily.POST_TOOL,
            migration_triggered_hook(stderr),
            frozenset({MAKEMIGRATIONS}),
        )
    )
    registry.register(
        HookRegistration(
            POST_GENERATION,
            HookFamily.POST_TOOL,
            post_generation_hook(clock, stderr, client_check),
            GENERATION_TOOLS,
        )
    )
    registry.register(
        HookRegistration(
            SESSION_STOP,
            HookFamily.SESSION_STOP,
            session_stop_hook(clock, stderr),
        )
    )
    return registry
