"""Real-tools end-to-end flow: DRF schema export, a generated Angular app, and a browser.

Nothing here is mocked. The flow installs the bundled tutorial project, exports its
OpenAPI schema with the real ``drf-spectacular``, creates an Angular workspace and
application with the real Angular CLI and ``angular-django2`` (ngdj), generates the API
client with ``ng-openapi-gen``, builds the application, serves it next to Django and
drives it with Playwright. It is the runnable-behavior part of the staged verification
(``doc/plan/VERIFICATION_PLAN.md``); ngdj's schematic tests stay in ngdj.

Run it with::

    DJNG_E2E=1 python -m tests.e2e.run_e2e

It takes minutes and needs Node, pnpm and a browser, so it is opt-in: without
``DJNG_E2E=1`` the default ``unittest discover`` reports it as skipped. CONTRIBUTING.md
lists the prerequisites. Environment variables:

``E2E_TRACKS``
    Comma-separated tracks to run, ``W`` (the wrappers directly) and ``B``
    (``build_app`` phase 2). Default ``W,B``.
``E2E_NGDJ_TARBALL``
    Path of a locally packed ngdj (``npm pack ./projects/angular-django2/dist``) to
    install instead of the pinned registry release.
``E2E_KEEP``
    ``1`` keeps the temporary area.
``E2E_ANGULAR_CLI``
    Version range of the Angular CLI installed when ``ng`` is not on ``PATH``
    (default ``^22``).
``E2E_CHROMIUM_PATH``
    Chromium executable for Playwright instead of its own download.
``E2E_PLAYWRIGHT_INSTALL``
    ``1`` runs ``playwright install chromium`` first.
``E2E_BREAK``
    ``model-field``, ``openui-route`` or ``proxy`` injects a deliberate break; the run
    must fail at the stage that names it.

Every command's argv, exit code and output, the exported schemas, the ``build_app`` dry
run and run, tool versions, the generated tree, the Playwright report and traces and
screenshots go to ``build/e2e-evidence/``. A failure names its stage.
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from collections.abc import Iterator
from dataclasses import dataclass, field
from importlib import metadata
from pathlib import Path
from typing import Any

from django_angular3 import tools
from django_angular3.angular import build_ngdj_schematic_invocations
from django_angular3.config import load_project_config
from django_angular3.settings import load_angular_settings
from django_angular3.step_bridge import stage_document, workspace_document_path
from tests.workspace_temp import WORKSPACE_TEMP_DIR, keep_workspace_temp

REPOSITORY = Path(__file__).resolve().parents[2]
E2E_DIR = Path(__file__).resolve().parent
FIXTURES = E2E_DIR / "fixtures"
EVIDENCE_DIR = REPOSITORY / "build" / "e2e-evidence"

PROJECT = "simple_crm"
SETTINGS_MODULE = f"{PROJECT}.settings"
PROJECT_CONFIG = f"django-angular3-{PROJECT}.json"
TOOL_CONFIG = "django-angular3.json"
DJANGO_URL = "http://127.0.0.1:8000"
ANGULAR_URL = "http://127.0.0.1:4200"

CUSTOMER_COUNT = 25
PRODUCT_COUNT = 12
EXPECTED_PATHS = {
    "/api/v1/customers/",
    "/api/v1/customers/{id}/",
    "/api/v1/products/",
}
EXPECTED_SCHEMAS = {
    "Customer": {"id", "name", "email", "phone", "active"},
    "PaginatedCustomerList": {"count", "next", "previous", "results"},
    "PaginatedProductList": {"count", "next", "previous", "results"},
    "PatchedCustomer": {"id", "name", "email", "phone", "active"},
    "Product": {"id", "name", "price", "sku"},
}
BREAKS = ("model-field", "openui-route", "proxy")
# The names the generated client uses for the tutorial's resources, read once from a
# real run of ng-openapi-gen 1.x and pinned here.
CLIENT_FILES = (
    "api.ts",
    "api-configuration.ts",
    "models/customer.ts",
    "models/product.ts",
    "fn/customers/customers-list.ts",
    "fn/products/products-list.ts",
)

# A page added by phase 2 of Track B, and a schema appended through the tool config.
ADDED_PAGE_ID = "reportsPage"
ADDED_SCHEMA = {
    "Health": {"type": "object", "properties": {"status": {"type": "string"}}}
}

_OUTPUT_TAIL = 4000
_CI_MARKERS = (
    "CI",
    "CONTINUOUS_INTEGRATION",
    "BUILD_NUMBER",
    "RUN_ID",
    "GITHUB_ACTIONS",
)
_NODE_VERSION = re.compile(r"v?(\d+)\.(\d+)\.(\d+)")


class StageFailure(AssertionError):
    """A stage of the flow failed; the message starts with the stage's name."""


@dataclass
class CommandRecord:
    index: int
    stage: str
    label: str
    argv: list[str]
    cwd: str
    returncode: int | None
    seconds: float
    log: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "stage": self.stage,
            "label": self.label,
            "argv": self.argv,
            "cwd": self.cwd,
            "exitCode": self.returncode,
            "seconds": round(self.seconds, 2),
            "log": self.log,
        }


@dataclass
class StageRecord:
    name: str
    status: str = "running"
    seconds: float = 0.0
    error: str | None = None


@dataclass
class Flow:
    """The state of one run: paths, environment, evidence and the stages in order."""

    tracks: frozenset[str]
    break_name: str
    work: Path = field(init=False)
    env: dict[str, str] = field(init=False)
    commands: list[CommandRecord] = field(default_factory=list)
    stages: list[StageRecord] = field(default_factory=list)
    findings: list[dict[str, str]] = field(default_factory=list)
    current_stage: str = "setup"
    last_error: str | None = None
    generated_client: Path = field(init=False)

    # -- paths -------------------------------------------------------------------------

    @property
    def project(self) -> Path:
        return self.work / PROJECT

    @property
    def project_config(self) -> Path:
        return self.project / PROJECT_CONFIG

    @property
    def tool_config(self) -> Path:
        return self.project / TOOL_CONFIG

    @property
    def schema(self) -> Path:
        return self.project / "schema.json"

    @property
    def document(self) -> Path:
        return self.project / "customers.openui.json"

    @property
    def workspace(self) -> Path:
        return self.project / "build" / "angular"

    @property
    def app_root(self) -> Path:
        return self.workspace / "projects" / PROJECT / "src" / "app"

    # -- stage and command plumbing ----------------------------------------------------

    @contextlib.contextmanager
    def stage(self, name: str) -> Iterator[None]:
        record = StageRecord(name)
        self.stages.append(record)
        self.current_stage = name
        started = time.monotonic()
        print(f"\n=== stage {name} ===", flush=True)
        try:
            yield
        except StageFailure:
            record.status, record.error = "failed", self.last_error
            raise
        except BaseException as exc:
            record.status = "failed"
            record.error = f"{type(exc).__name__}: {exc}"
            raise StageFailure(f"[stage {name}] {record.error}") from exc
        else:
            record.status = "passed"
        finally:
            record.seconds = time.monotonic() - started

    def fail(self, message: str) -> StageFailure:
        self.last_error = message
        return StageFailure(f"[stage {self.current_stage}] {message}")

    def check(self, condition: object, message: str) -> None:
        if not condition:
            raise self.fail(message)

    def run(
        self,
        argv: list[str],
        *,
        cwd: Path,
        label: str,
        check: bool = True,
        timeout: int = 1800,
        extra_env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """Run one command, record argv, exit code and output, and check the exit code."""
        env = {**self.env, **(extra_env or {})}
        executable = shutil.which(argv[0], path=env["PATH"])
        command = [executable or argv[0], *argv[1:]]
        index = len(self.commands) + 1
        log_dir = EVIDENCE_DIR / "commands"
        log_dir.mkdir(parents=True, exist_ok=True)
        slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")[:60]
        log_path = log_dir / f"{index:03d}-{slug}.log"
        print(f"$ {' '.join(command)}   (in {cwd})", flush=True)
        started = time.monotonic()
        try:
            completed = subprocess.run(
                command,
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            returncode: int | None = None
            completed = subprocess.CompletedProcess(command, -1, "", str(exc))
        else:
            returncode = completed.returncode
        seconds = time.monotonic() - started
        log_path.write_text(
            f"$ {' '.join(command)}\n# cwd: {cwd}\n# exit code: {returncode}\n"
            f"\n--- stdout ---\n{completed.stdout}\n--- stderr ---\n{completed.stderr}\n",
            encoding="utf-8",
        )
        self.commands.append(
            CommandRecord(
                index,
                self.current_stage,
                label,
                argv,
                str(cwd),
                returncode,
                seconds,
                log_path.relative_to(EVIDENCE_DIR).as_posix(),
            )
        )
        if check and completed.returncode != 0:
            tail = (completed.stderr.strip() or completed.stdout.strip())[
                -_OUTPUT_TAIL:
            ]
            raise self.fail(
                f"{label} failed (exit code {returncode}): {' '.join(argv)}\n{tail}"
            )
        return completed

    def manage(self, *arguments: str, label: str | None = None, **kwargs: Any):
        """Run a management command of the project, as a generated app does."""
        return self.run(
            [sys.executable, "manage.py", *arguments],
            cwd=self.project,
            label=label or f"manage.py {arguments[0]}",
            **kwargs,
        )

    def djng(self, *arguments: str, label: str):
        return self.run(
            [sys.executable, "-m", "django_angular3", *arguments],
            cwd=self.project,
            label=label,
        )

    # -- file helpers ------------------------------------------------------------------

    def read_json(self, path: Path) -> Any:
        return json.loads(path.read_text(encoding="utf-8"))

    def write_json(self, path: Path, document: Any) -> None:
        path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

    def replace_once(self, path: Path, old: str, new: str) -> None:
        """Edit a generated file; its layout changing is a failure of the stage."""
        text = path.read_text(encoding="utf-8")
        self.check(
            text.count(old) == 1,
            f"{path.name} no longer has exactly one {old!r}; the generated layout "
            "changed and the host glue cannot be wired.",
        )
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    # -- stage 0 -----------------------------------------------------------------------

    def stage_0_environment(self) -> None:
        self.check(
            sys.version_info >= (3, 12), f"Python 3.12+ is required: {sys.version}"
        )
        WORKSPACE_TEMP_DIR.mkdir(exist_ok=True)
        self.work = Path(tempfile.mkdtemp(prefix="e2e-", dir=WORKSPACE_TEMP_DIR))
        env = dict(os.environ)
        env.update(
            DJANGO_SETTINGS_MODULE=SETTINGS_MODULE,
            NG_CLI_ANALYTICS="false",
            PYTHONUNBUFFERED="1",
            PYTHONIOENCODING="utf-8",
            NO_COLOR="1",
            FORCE_COLOR="0",
        )
        # In a CI environment pnpm refuses an install that must update the lockfile,
        # which every schematic that adds a dependency does, and no setting overrides
        # that default for the install the Angular CLI runs. The tools run as locally.
        for marker in _CI_MARKERS:
            env.pop(marker, None)
        self.env = env

        node = self.run(["node", "--version"], cwd=REPOSITORY, label="node --version")
        self.check(
            _node_supported(node.stdout.strip()),
            f"Node {node.stdout.strip()} is not supported by ngdj "
            "(^22.22.3 || ^24.15.0 || >=26).",
        )
        self.run(["pnpm", "--version"], cwd=REPOSITORY, label="pnpm --version")
        self.run(["npm", "--version"], cwd=REPOSITORY, label="npm --version")
        self._ensure_angular_cli()
        self.check(
            _installed_version("django-angular3"), "django-angular3 is not installed."
        )
        if "B" in self.tracks:
            try:
                path = tools.ensure_oasdiff()
            except RuntimeError as exc:
                raise self.fail(
                    f"oasdiff is not available ({exc}). Pre-install it once with "
                    "python -c 'from django_angular3.tools import ensure_oasdiff; "
                    "ensure_oasdiff()' and cache django_angular3/.bin."
                ) from exc
            self.run([path, "--version"], cwd=REPOSITORY, label="oasdiff --version")

    def _ensure_angular_cli(self) -> None:
        if shutil.which("ng", path=self.env["PATH"]):
            self.run(["ng", "version"], cwd=self.work, label="ng version")
            return
        spec = os.environ.get("E2E_ANGULAR_CLI", "^22")
        prefix = self.work / "tools"
        prefix.mkdir()
        self.run(
            ["npm", "install", "--prefix", str(prefix), f"@angular/cli@{spec}"],
            cwd=self.work,
            label="npm install @angular/cli",
        )
        self.env["PATH"] = os.pathsep.join(
            [str(prefix / "node_modules" / ".bin"), self.env["PATH"]]
        )
        self.run(["ng", "version"], cwd=self.work, label="ng version")

    # -- stage 1 -----------------------------------------------------------------------

    def stage_1_backend(self) -> None:
        self.run(
            [
                sys.executable,
                "-m",
                "django_angular3",
                "install-tutorial",
                str(self.project),
            ],
            cwd=self.work,
            label="django-angular3 install-tutorial",
        )
        config = self.read_json(self.project_config)
        config["artifacts"]["openapiSchema"] = "schema.json"
        config["artifacts"]["openuiSpecification"] = self.document.name
        self.write_json(self.project_config, config)

        tarball = os.environ.get("E2E_NGDJ_TARBALL")
        if tarball:
            tarball_path = Path(tarball).resolve()
            self.check(tarball_path.is_file(), f"E2E_NGDJ_TARBALL not found: {tarball}")
            tool = self.read_json(self.tool_config)
            tool["tool"]["ngAddPackage"] = str(tarball_path)
            self.write_json(self.tool_config, tool)

        document = self.read_json(FIXTURES / "customers.openui.json")
        if self.break_name == "openui-route":
            _remove_products_route(document)
        self.write_json(self.document, document)

        self.manage("check", label="manage.py check")
        self.manage("migrate", "--noinput", label="manage.py migrate")
        self.manage("loaddata", str(FIXTURES / "seed.json"), label="manage.py loaddata")
        counts = self.manage(
            "shell",
            "-c",
            "from shop.models import Customer, Product; "
            "print('seed-counts', Customer.objects.count(), Product.objects.count())",
            label="manage.py shell (seed counts)",
        )
        self.check(
            f"seed-counts {CUSTOMER_COUNT} {PRODUCT_COUNT}"
            in counts.stdout.splitlines(),
            f"The seed loaded {counts.stdout.strip()!r}, expected {CUSTOMER_COUNT} "
            f"customers and {PRODUCT_COUNT} products.",
        )

    # -- stage 2 -----------------------------------------------------------------------

    def stage_2_export_schema(self) -> None:
        if self.break_name == "model-field":
            for name in ("models.py", "serializers.py"):
                path = self.project / "shop" / name
                path.write_text(
                    re.sub(
                        r"\bphone\b", "phone_number", path.read_text(encoding="utf-8")
                    ),
                    encoding="utf-8",
                )

        self.manage("export_schema", label="manage.py export_schema")
        schema = self.read_json(self.schema)
        self.djng(
            "validate-openapi", str(self.schema), label="validate-openapi schema.json"
        )

        self.check(
            set(schema["paths"]) == EXPECTED_PATHS,
            f"The exported paths are {sorted(schema['paths'])}, expected "
            f"{sorted(EXPECTED_PATHS)}.",
        )
        components = schema["components"]["schemas"]
        self.check(
            set(components) == set(EXPECTED_SCHEMAS),
            f"The exported schemas are {sorted(components)}, expected "
            f"{sorted(EXPECTED_SCHEMAS)}.",
        )
        for name, properties in EXPECTED_SCHEMAS.items():
            self.check(
                set(components[name]["properties"]) == properties,
                f"Schema {name} has the properties "
                f"{sorted(components[name]['properties'])}, expected {sorted(properties)}.",
            )
        # The info block comes from drfSpectacular.settings of django-angular3.json: the
        # tool configuration replaces SPECTACULAR_SETTINGS for the export.
        expected_info = self.read_json(self.tool_config)["drfSpectacular"]["settings"]
        self.check(
            schema["info"]
            == {"title": expected_info["TITLE"], "version": expected_info["VERSION"]},
            f"info is {schema['info']}, but drfSpectacular.settings says "
            f"{expected_info['TITLE']!r} {expected_info['VERSION']!r}.",
        )

        previous = self.schema.with_name("schema.previous.json")
        self.check(
            not previous.exists(), "schema.previous.json exists before a rotation."
        )
        first = self.schema.read_bytes()
        self.manage("export_schema", label="manage.py export_schema (second)")
        self.check(
            previous.is_file(), "A second export did not create schema.previous.json."
        )
        self.check(
            previous.read_bytes() == first, "The rotated schema differs from the first."
        )
        self.check(
            self.schema.read_bytes() == first, "Two exports of the same project differ."
        )
        self._copy_evidence(self.schema, "exported/schema.json")
        self._copy_evidence(previous, "exported/schema.previous.json")

    # -- stage 3 -----------------------------------------------------------------------

    def stage_3_workspace_and_client(self) -> None:
        self.djng(
            "validate-openui",
            str(self.document),
            label="validate-openui customers.openui.json",
        )
        self.manage("ng_workspace", label="manage.py ng_workspace")
        angular_json = self.workspace / "angular.json"
        self.check(angular_json.is_file(), "ng_workspace created no angular.json.")
        package = self.workspace / "node_modules" / "angular-django2" / "package.json"
        self.check(package.is_file(), "ng add did not install angular-django2.")
        installed = self.read_json(package)["version"]
        pinned = self.read_json(self.tool_config)["tool"]["ngAddPackage"]
        if "@" in pinned and not os.environ.get("E2E_NGDJ_TARBALL"):
            self.check(
                pinned.endswith(f"@{installed}"),
                f"angular-django2 {installed} is installed, but ngAddPackage is {pinned}.",
            )
        elif os.environ.get("E2E_NGDJ_TARBALL"):
            # build_app locates the package by name and version, not by tarball path.
            tool = self.read_json(self.tool_config)
            tool["tool"]["ngAddPackage"] = f"angular-django2@{installed}"
            self.write_json(self.tool_config, tool)

        config = load_project_config(self.project_config)
        stage_document(config)
        relative = workspace_document_path(config)
        self.manage(
            "ng_gen_app",
            "--document",
            relative,
            label="manage.py ng_gen_app --document",
        )
        self.check(
            (self.app_root / "app.ts").is_file(),
            f"ng_gen_app generated no application {PROJECT} (no src/app/app.ts).",
        )

        helpers = f"projects/{PROJECT}/src/app/api-integration"
        self.manage(
            "ng_openapi_setup",
            "--output-path",
            f"projects/{PROJECT}/src/app/api",
            "--helpers-path",
            helpers,
            "--skip-tests",
            label="manage.py ng_openapi_setup",
        )
        self.run(
            ["pnpm", "install", "--no-frozen-lockfile"],
            cwd=self.workspace,
            label="pnpm install",
        )
        self.manage("ng_openapi_gen", label="manage.py ng_openapi_gen")

        generated = self.read_json(self.workspace / "ng-openapi-gen.json")
        output = self.workspace / generated["output"]
        self.check(
            output == self.app_root / "api",
            f"ng-openapi-gen.json names {output}, not the {self.app_root / 'api'} that "
            "ng_openapi_setup configured inside the application project.",
        )
        for name in CLIENT_FILES:
            self.check(
                (output / name).is_file(),
                f"ng-openapi-gen generated no {name} in {output}.",
            )
        self.check(
            "export interface Customer"
            in (output / "models/customer.ts").read_text(encoding="utf-8")
            and "export interface Product"
            in (output / "models/product.ts").read_text(encoding="utf-8"),
            "The generated Customer and Product models are not the expected interfaces.",
        )
        self.check(
            (self.app_root / "api-integration" / "django-transport.ts").is_file(),
            "ng_openapi_setup generated no api-integration/django-transport.ts.",
        )
        self.generated_client = output
        for resource in ("customers", "products"):
            service = output / "services" / f"{resource}-api.service.ts"
            self.check(
                service.is_file()
                and f"export class {resource.capitalize()}ApiService"
                in service.read_text(encoding="utf-8"),
                f"ng-openapi-gen generated no {resource.capitalize()}ApiService in "
                f"{service}; the ngdj data-service schematic wraps that class.",
            )

    # -- stage 4 -----------------------------------------------------------------------

    def stage_4_ui(self) -> None:
        config = load_project_config(self.project_config)
        relative = workspace_document_path(config)
        for page in ("customers", "products"):
            name = f"{page}-page"
            self.manage(
                "ng_page",
                "--name",
                name,
                "--target-path",
                f"src/app/features/{name}",
                "--project",
                PROJECT,
                "--document",
                relative,
                "--node-id",
                f"{page}Page",
                label=f"manage.py ng_page {name}",
            )
            self.check(
                (
                    self.app_root / "features" / name / f"{name}.page.routes.ts"
                ).is_file(),
                f"ng_page generated no routes for {name}.",
            )

        # build_app runs the table schematic as a step; no operator wrapper exists, so the
        # flow resolves the same invocation through djng.
        settings = load_angular_settings(config_path=self.tool_config)
        (table,) = build_ngdj_schematic_invocations(
            config,
            settings,
            schematic="table",
            document=relative,
            node_id="customers",
            project=PROJECT,
        )
        self.run(
            list(table.argv), cwd=table.cwd, label="ng generate angular-django2:table"
        )
        table_dir = self.app_root / "shared" / "tables" / "customers-table"
        self.check(
            (table_dir / "customers-table.ts").is_file(),
            "The table schematic generated no table.",
        )

        self.manage(
            "ng_data_service",
            "--resource",
            "customers",
            "--path",
            f"projects/{PROJECT}/src/app/features/customers/services",
            label="manage.py ng_data_service --path",
        )
        service = next(self.workspace.glob("**/customers.data.service.ts"), None)
        self.check(
            service is not None and "node_modules" not in service.parts,
            "ng_data_service generated no customers.data.service.ts.",
        )
        if service is not None:
            self.check(
                service.is_relative_to(self.app_root),
                f"ng_data_service --path wrote {service.relative_to(self.workspace)}, "
                f"outside the application project {self.app_root}.",
            )
            # The service imports the generated services from ../api/services,
            # relative to its own directory, so inside the project it breaks the build.
            shutil.rmtree(service.parent)
            self.findings.append(
                {
                    "id": "data-service-not-buildable",
                    "title": "The generated data service does not compile",
                    "detail": "customers.data.service.ts imports CustomersApiService "
                    "from ../api/services, relative to its own directory, while the "
                    "generated client is in the application's api directory; the "
                    "ng_data_service wrapper has no --api-path (ngdj apiPath). The flow "
                    "removes the service after asserting its location, before the build.",
                }
            )

        self._wire_host_glue()
        self.findings.append(
            {
                "id": "no-generated-error-state",
                "title": "No generated artifact shows a failed list request",
                "detail": "The generated ResourceAdapter only logs the failure "
                "(console.error). P4 asserts that log and the error state of the "
                "host glue (tests/e2e/fixtures/customers-host.ts).",
            }
        )

    def _wire_host_glue(self) -> None:
        """Copy the host glue next to the customers page and wire it in.

        The glue is a committed test fixture, not generated: it feeds the generated
        table from the generated client. The page, the application configuration and the
        generated client's import path are the only edits.
        """
        page_dir = self.app_root / "features" / "customers-page"
        relative_client = os.path.relpath(self.generated_client, page_dir).replace(
            os.sep, "/"
        )
        glue = (FIXTURES / "customers-host.ts").read_text(encoding="utf-8")
        (page_dir / "customers-host.ts").write_text(
            glue.replace("__GENERATED_API__", relative_client), encoding="utf-8"
        )
        self.replace_once(
            page_dir / "customers-page-page.html",
            "<!-- End children section -->",
            "<!-- End children section -->\n    <app-customers-host />",
        )
        page = page_dir / "customers-page-page.ts"
        self.replace_once(
            page,
            "import { MatCardModule } from '@angular/material/card';",
            "import { MatCardModule } from '@angular/material/card';\n"
            "import { CustomersHostComponent } from './customers-host';",
        )
        self.replace_once(
            page,
            "imports: [MatCardModule]",
            "imports: [MatCardModule, CustomersHostComponent]",
        )

        config = self.app_root / "app.config.ts"
        self.replace_once(
            config,
            "import { routes } from './app.routes';",
            "import { routes } from './app.routes';\n"
            "import { provideDjangoApiTransport } from './api-integration';",
        )
        self.replace_once(
            config, "providers: [", "providers: [provideDjangoApiTransport(), "
        )

    # -- stage 5 -----------------------------------------------------------------------

    def stage_5_build(self) -> None:
        self.manage("ng_build", label="manage.py ng_build")
        dist = self.workspace / "dist"
        files = (
            [path for path in dist.rglob("*") if path.is_file()]
            if dist.is_dir()
            else []
        )
        self.check(files, f"ng_build left no files in {dist}.")
        self.check(
            any(path.name == "index.html" for path in files),
            f"The build in {dist} has no index.html.",
        )

    # -- stage 6 -----------------------------------------------------------------------

    def stage_6_browser(self) -> None:
        proxy = self.read_json(FIXTURES / "proxy.conf.json")
        if self.break_name == "proxy":
            proxy["/api"]["target"] = "http://127.0.0.1:9"
        self.write_json(self.workspace / "proxy.conf.json", proxy)

        self.run(
            ["npm", "ci", "--no-audit", "--no-fund"],
            cwd=E2E_DIR,
            label="npm ci (Playwright)",
        )
        if os.environ.get("E2E_PLAYWRIGHT_INSTALL") == "1":
            self.run(
                ["npx", "--no-install", "playwright", "install", "chromium"],
                cwd=E2E_DIR,
                label="playwright install chromium",
            )
        self.run(
            ["npx", "--no-install", "tsc", "-p", "tsconfig.json"],
            cwd=E2E_DIR,
            label="tsc (Playwright specs)",
        )
        self.run(
            ["npx", "--no-install", "playwright", "test"],
            cwd=E2E_DIR,
            label="playwright test",
            extra_env={
                "E2E_PYTHON": sys.executable,
                "E2E_PROJECT_DIR": str(self.project),
                "E2E_WORKSPACE_DIR": str(self.workspace),
                "E2E_APPLICATION": PROJECT,
                "E2E_EVIDENCE_DIR": str(EVIDENCE_DIR),
                "E2E_DJANGO_URL": DJANGO_URL,
                "E2E_ANGULAR_URL": ANGULAR_URL,
                "E2E_SEED": str(FIXTURES / "seed.json"),
                "E2E_SETTINGS_MODULE": SETTINGS_MODULE,
            },
            timeout=1500,
        )

    # -- track B, phase 2 --------------------------------------------------------------

    def stage_b_build_app(self) -> None:
        """Change the OpenUI document and the OpenAPI schema; let build_app derive the steps.

        Phase 1 as a ``build_app`` run (workspace and application from nothing) waits on
        django-angular3#209 and previous-configuration discovery, so this track starts
        from the workspace Track W created.
        """
        baseline = self.project / "baseline"
        baseline.mkdir()
        shutil.copyfile(self.document, baseline / self.document.name)
        baseline_config = {
            "project": {"name": PROJECT},
            "artifacts": {
                "openapiSchema": "../schema.previous.json",
                "openuiSpecification": self.document.name,
                "angularWorkspace": "../build/angular",
            },
        }
        self.write_json(baseline / "django-angular3-baseline.json", baseline_config)

        # The schema change: a component appended through the tool configuration. The
        # export rotates the Track W schema to schema.previous.json, the baseline.
        tool = self.read_json(self.tool_config)
        tool["drfSpectacular"]["settings"]["APPEND_COMPONENTS"] = {
            "schemas": ADDED_SCHEMA
        }
        self.write_json(self.tool_config, tool)
        self.manage("export_schema", label="manage.py export_schema (phase 2)")
        schema = self.read_json(self.schema)
        self.check(
            set(schema["components"]["schemas"])
            == set(EXPECTED_SCHEMAS) | set(ADDED_SCHEMA),
            "The phase 2 export did not add the appended schema.",
        )
        previous = self.read_json(self.schema.with_name("schema.previous.json"))
        self.check(
            set(previous["components"]["schemas"]) == set(EXPECTED_SCHEMAS),
            "schema.previous.json is not the Track W schema.",
        )

        # The OpenUI change: one more page.
        document = self.read_json(self.document)
        document["children"].append(
            {
                "id": ADDED_PAGE_ID,
                "type": "DashboardPage",
                "attrs": {"uses.route": '"reports"', "uses.title": '"Reports"'},
            }
        )
        self.write_json(self.document, document)
        self.djng(
            "validate-openui", str(self.document), label="validate-openui (phase 2)"
        )

        previous_config = str(baseline / "django-angular3-baseline.json")
        dry = self.manage(
            "build_app",
            "--previous-config",
            previous_config,
            "--dry-run",
            label="manage.py build_app --dry-run",
        )
        dry_run = json.loads(dry.stdout)
        self._copy_text(dry.stdout, "build-app/dry-run.json")
        self.check(
            dry_run["dryRun"] is True, "The build_app dry run is not marked dryRun."
        )
        steps = dry_run["steps"]
        derived = [(step["step"], step["command"]) for step in steps]
        self.check(
            ("ngdj_add_page", "ng_page") in derived,
            f"The dry run derived no ng_page step for {ADDED_PAGE_ID}: {derived}.",
        )
        self.check(
            ("angular_api_client_generate", "ng_openapi_gen") in derived,
            f"The dry run derived no ng_openapi_gen step for the new schema: {derived}.",
        )
        self.check(
            steps[-1]["step"] == "last-check" and steps[-1]["command"] == "ng_build",
            f"The dry run does not end with the build gate: {derived}.",
        )
        self.check(
            not any(step["unresolved"] for step in steps),
            f"The dry run left options unresolved: {derived}.",
        )
        pages = [s for s in steps if s["command"] == "ng_page"]
        self.check(
            [s["nodeId"] for s in pages] == [ADDED_PAGE_ID],
            f"The dry run derives pages for {[s['nodeId'] for s in pages]}, expected only "
            f"{ADDED_PAGE_ID}.",
        )

        self.manage(
            "build_app",
            "--previous-config",
            previous_config,
            label="manage.py build_app",
            timeout=2400,
        )
        evidence_path = self.project / "build" / "build-evidence.json"
        self.check(
            evidence_path.is_file(), "build_app wrote no build/build-evidence.json."
        )
        evidence = self.read_json(evidence_path)
        self._copy_evidence(evidence_path, "build-app/build-evidence.json")
        statuses = [(step["step"], step.get("status")) for step in evidence["steps"]]
        self.check(
            statuses and all(status == "succeeded" for _, status in statuses),
            f"Not every build_app step succeeded: {statuses}.",
        )
        self.check(
            evidence["dryRun"] is False, "The build_app evidence is marked dryRun."
        )
        installed = self.read_json(
            self.workspace / "node_modules" / "angular-django2" / "package.json"
        )["version"]
        self.check(
            evidence["ngdj"]["package"] == f"angular-django2@{installed}"
            and evidence["ngdj"]["mappingVersion"] == 1
            and evidence["ngdj"]["openuiSpecVersion"],
            f"The build_app evidence does not pin the ngdj package and mapping: {evidence['ngdj']}.",
        )
        self.check(
            (
                self.app_root
                / "features"
                / "reports-page"
                / "reports-page.page.routes.ts"
            ).is_file(),
            "build_app generated no reports-page.",
        )

    # -- stage 7 -----------------------------------------------------------------------

    def stage_7_evidence(self) -> None:
        """Write the summary, versions and the generated tree. Never raises."""
        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        with contextlib.suppress(Exception):
            self.write_json(EVIDENCE_DIR / "tool-versions.json", self._tool_versions())
        with contextlib.suppress(Exception):
            tree = self._generated_tree()
            (EVIDENCE_DIR / "generated-tree.txt").write_text(tree, encoding="utf-8")
        self.write_json(
            EVIDENCE_DIR / "commands.json", [c.to_dict() for c in self.commands]
        )
        self.write_json(
            EVIDENCE_DIR / "summary.json",
            {
                "tracks": sorted(self.tracks),
                "break": self.break_name or None,
                "stages": [
                    {
                        "name": s.name,
                        "status": s.status,
                        "seconds": round(s.seconds, 1),
                        "error": s.error,
                    }
                    for s in self.stages
                ],
                "findings": self.findings,
                "temporaryArea": str(self.work) if hasattr(self, "work") else None,
            },
        )

    def _tool_versions(self) -> dict[str, str | None]:
        def output(argv: list[str], cwd: Path) -> str | None:
            executable = shutil.which(argv[0], path=self.env["PATH"])
            if executable is None:
                return None
            done = subprocess.run(
                [executable, *argv[1:]],
                cwd=cwd,
                env=self.env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            return (done.stdout or done.stderr).strip() or None

        def package_version(workspace_package: str) -> str | None:
            path = self.workspace / "node_modules" / workspace_package / "package.json"
            return self.read_json(path)["version"] if path.is_file() else None

        angular = output(
            ["ng", "version"], self.workspace if self.workspace.is_dir() else REPOSITORY
        )
        match = re.search(r"Angular CLI\s*:\s*(\S+)", angular or "")
        return {
            "python": sys.version.split()[0],
            "django-angular3": _installed_version("django-angular3"),
            "openui-spec": _installed_version("openui-spec"),
            "django": _installed_version("django"),
            "djangorestframework": _installed_version("djangorestframework"),
            "drf-spectacular": _installed_version("drf-spectacular"),
            "angular-django2": package_version("angular-django2"),
            "ng-openapi-gen": package_version("ng-openapi-gen"),
            "node": output(["node", "--version"], REPOSITORY),
            "pnpm": output(["pnpm", "--version"], REPOSITORY),
            "angular-cli": match.group(1) if match else None,
            "playwright": output(
                ["npx", "--no-install", "playwright", "--version"], E2E_DIR
            ),
            "oasdiff": output([tools.ensure_oasdiff(), "--version"], REPOSITORY)
            if "B" in self.tracks
            else None,
        }

    def _generated_tree(self) -> str:
        skipped = {"node_modules", ".angular", ".git"}
        lines: list[str] = []
        for root, directories, files in os.walk(self.project):
            directories[:] = sorted(d for d in directories if d not in skipped)
            for name in sorted(files):
                path = Path(root) / name
                relative = path.relative_to(self.project).as_posix()
                lines.append(f"{path.stat().st_size:>10}  {relative}")
        return "\n".join(lines) + "\n"

    def _copy_evidence(self, source: Path, relative: str) -> None:
        target = EVIDENCE_DIR / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)

    def _copy_text(self, text: str, relative: str) -> None:
        target = EVIDENCE_DIR / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    # -- the flow ----------------------------------------------------------------------

    def execute(self) -> None:
        sequence = [
            ("0 environment", self.stage_0_environment),
            ("1 backend", self.stage_1_backend),
            ("2 export-schema", self.stage_2_export_schema),
            ("3 workspace-and-client", self.stage_3_workspace_and_client),
            ("4 ui-from-openui", self.stage_4_ui),
            ("5 build", self.stage_5_build),
            ("6 browser", self.stage_6_browser),
        ]
        if "B" in self.tracks:
            sequence.append(("B build_app phase 2", self.stage_b_build_app))
        try:
            for name, method in sequence:
                with self.stage(name):
                    method()
        finally:
            self.current_stage = "7 evidence"
            self.stage_7_evidence()


def _node_supported(version: str) -> bool:
    """True for ``^22.22.3 || ^24.15.0 || >=26`` (the ngdj and Angular CLI engines)."""
    match = _NODE_VERSION.fullmatch(version.strip())
    if match is None:
        return False
    major, minor, patch = (int(part) for part in match.groups())
    if major == 22:
        return (minor, patch) >= (22, 3)
    if major == 24:
        return (minor, patch) >= (15, 0)
    return major >= 26


def _installed_version(distribution: str) -> str | None:
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return None


def _remove_products_route(document: dict[str, Any]) -> None:
    """The ``openui-route`` break: drop the products route and its navigation item."""
    removed = {"productsRoute", "productsNavigation"}

    def prune(element: dict[str, Any]) -> None:
        element["children"] = [
            child for child in element.get("children", []) if child["id"] not in removed
        ]
        for child in element["children"]:
            prune(child)

    prune(document)


@unittest.skipUnless(
    os.environ.get("DJNG_E2E") == "1",
    "Slow real-tools flow: set DJNG_E2E=1 (see tests/e2e/run_e2e.py).",
)
class RealToolsEndToEndTests(unittest.TestCase):
    maxDiff = None

    def test_track_w_and_b(self) -> None:
        tracks = frozenset(
            track.strip().upper()
            for track in os.environ.get("E2E_TRACKS", "W,B").split(",")
            if track.strip()
        )
        self.assertTrue(
            tracks and tracks <= {"W", "B"}, f"E2E_TRACKS: {sorted(tracks)}"
        )
        break_name = os.environ.get("E2E_BREAK", "")
        self.assertIn(break_name, ("", *BREAKS), f"E2E_BREAK must be one of {BREAKS}.")

        if os.environ.get("E2E_KEEP") == "1":
            keep_workspace_temp()
        if EVIDENCE_DIR.exists():
            shutil.rmtree(EVIDENCE_DIR)
        EVIDENCE_DIR.mkdir(parents=True)

        Flow(tracks=tracks, break_name=break_name).execute()


if __name__ == "__main__":
    unittest.main(module=sys.modules[__name__], verbosity=2)
