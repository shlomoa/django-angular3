# Contributing

## Assumptions

- You are running **Python 3.12 or later**. Check with `python --version`.
- You have **Git** installed and configured with your GitHub identity.
- You have cloned the repository and your working directory is the repo root.
- No Node.js, Angular CLI, or other frontend tooling is required to contribute
  to this repository. It is a Python-only package. Only the opt-in
  [end-to-end validation](#end-to-end-validation) needs them.

## Prerequisites

Before running any of the commands below, create and activate a virtual
environment:

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

Then install the package with development and documentation tooling:

```bash
python -m pip install -e ".[dev,docs]"
```

## Development setup

Install the project from source with development and documentation tooling covered in
[Prerequisites](#prerequisites) above.

The `dev` extra installs Ruff. The separate `docs` extra installs Sphinx,
the documentation theme, and parser extensions. Both are included in the
standard contributor setup because documentation builds are part of validation;
installing only `.[dev]` does not install the documentation toolchain.

If you also want YAML support for OpenAPI or UI definition files:

```bash
python -m pip install -e ".[dev,docs,yaml]"
```

## Local validation and build checks

The current scaffold is Python-only. Use the bundled project config to validate
the example inputs locally:

```bash
django-admin validate-project django-angular3.json
```

The bundled project config targets generated Angular artifacts under
`build/angular/` by default. No checked-in Angular package is required.

## Tests

Run the existing test suite with explicit discovery:

```bash
python -m unittest discover -s tests -p 'test*.py'
```

## End-to-end validation

The unit tests check generated command lines and use a stand-in `ng`. One opt-in
flow runs the real tools instead: it installs the tutorial project, exports its
schema with `drf-spectacular`, creates an Angular workspace and application with the
Angular CLI and `angular-django2` (ngdj), generates the API client with
`ng-openapi-gen`, builds the application, serves it next to Django and drives it
with Playwright, and finally serves the built application from Django alone. It does
not repeat ngdj's schematic tests.

```bash
DJNG_E2E=1 python -m tests.e2e.run_e2e
```

Without `DJNG_E2E=1` the default test discovery reports it as skipped. It takes
several minutes. Prerequisites:

- Python 3.12 or 3.13 with `python -m pip install -e ".[yaml]"`.
- Node `^22.22.3 || ^24.15.0`, `pnpm`, and an Angular CLI on `PATH` (otherwise the
  flow installs `@angular/cli@E2E_ANGULAR_CLI` into its temporary area).
- A Chromium for Playwright: `cd tests/e2e && npm ci && npx playwright install
  chromium`, or `E2E_PLAYWRIGHT_INSTALL=1`, or `E2E_CHROMIUM_PATH`.
- `oasdiff` cached once (Track B): `python -c "from django_angular3.tools import
  ensure_oasdiff; ensure_oasdiff()"`, or an `oasdiff` on `PATH`. It is downloaded from
  the GitHub releases, so pre-install it where egress is restricted.
- Ports 8000 (Django) and 4200 (Angular dev server) free.
- The flow removes the CI markers (`CI`, `GITHUB_ACTIONS`, ...) from the environment of
  the tools. Under them pnpm 10 refuses an install that has to update the lockfile, which
  every schematic that adds a dependency causes, and no setting overrides that for the
  install the Angular CLI runs itself.

The flow runs these stages; a failure names its stage:

| Stage | What it proves |
| :--- | :--- |
| 0 environment | Tool versions are supported |
| 1 backend | The tutorial installs, migrates and loads the seed (25 customers, 12 products) |
| 2 export-schema | `export_schema` with the real `drf-spectacular`: paths, schemas, `info`, rotation |
| 3 workspace-and-client | `ng_workspace`, `ng_gen_app`, `ng_openapi_setup`, `ng_openapi_gen` |
| 4 ui-from-openui | `ng_page`, the `table` schematic, `ng_data_service`, the host glue |
| 5 build | `ng_build` leaves a non-empty `dist/` |
| 6 browser | Playwright specs P1 shell, P2 data alignment, P3 pagination, P4 failure path, against `runserver` and the Angular dev server (proxy to Django) |
| 6b django-serves-build | Django alone serves the built bundle (`django_angular3.spa`, one origin, no proxy, no CORS): P1–P4 again plus D1 hard refresh on `/customers` and `/products`, D2 in-app navigation without a document request, D3 the API stays JSON and a wrong URL is a 404, D4 the admin stays Django, D5 one origin and no CORS headers, D6 assets served and a stale hash is a 404 |
| B build_app phase 2 | A changed OpenUI document and schema: the dry run derives the steps, the run succeeds |

Track B starts from the workspace the wrappers created; running `build_app` from
nothing waits on django-angular3#209 and previous-configuration discovery.

The fixtures in `tests/e2e/fixtures` are generated, not edited: run
`python -m tests.e2e.generate_fixtures`. `customers-host.ts` is the exception, a
hand-written host component marked as test glue, because nothing generated binds the
generated table to the generated client.

Environment variables:

| Variable | Effect |
| :--- | :--- |
| `E2E_TRACKS` | `W`, `B` or `W,B` (default) |
| `E2E_NGDJ_TARBALL` | Install a locally packed ngdj (`npm pack ./projects/angular-django2/dist`) instead of the pinned release |
| `E2E_KEEP=1` | Keep the temporary area under `scratch/` |
| `E2E_ANGULAR_CLI` | Angular CLI range installed when `ng` is missing (default `^22`) |
| `E2E_CHROMIUM_PATH` | Chromium executable for Playwright |
| `E2E_PLAYWRIGHT_INSTALL=1` | Run `playwright install chromium` first |
| `E2E_BREAK` | `model-field`, `openui-route`, `proxy` or `django-dist`: inject a deliberate break; the run must fail at stage 2, 6, 6 (P1, P2) and 6b respectively (`django-dist` moves the built bundle away from `ANGULAR_DIST_DIR`) |

The first run showed differences between what the tools do and what their documentation or
the flow's design assumed; they are recorded in
[`doc/plan/VERIFICATION_PLAN.md`](doc/plan/VERIFICATION_PLAN.md#first-slice-the-tutorial-flow)
and in the `findings` of `summary.json`.

Everything is written to `build/e2e-evidence/`: the exported schemas, the
`build_app` dry run and run, every command's argv, exit code and output, tool
versions, the generated tree, the Playwright report, traces and screenshots, and
`summary.json` with the findings of the run.

The `End-to-end` workflow (`.github/workflows/e2e.yml`) runs it on
`workflow_dispatch` (with a `break` input), nightly, and on pull requests that touch
`django_angular3/`, `tests/e2e/` or the workflow, and uploads the evidence and the
Playwright report as artifacts.

## Linting and formatting

```bash
ruff check django_angular3 tests
ruff format django_angular3 tests
```

Ruff is configured in `pyproject.toml` under `[tool.ruff]`. Both checks are
enforced by CI and must pass before a pull request can merge.

## CI/CD

CI is configured in `.github/workflows/`:

- `build.yml` — runs ruff lint/format checks, then the test suite and package
  build on every push and pull request to `main`.
- `e2e.yml` — runs the real-tools [end-to-end validation](#end-to-end-validation)
  on demand, nightly and on pull requests that touch the package or the flow.
- `deploy.yml` — builds and publishes the package to PyPI via Trusted
  Publishing when a GitHub Release is published.

Before opening a pull request, run linting, formatting checks, the test suite,
and the documentation build locally to
catch issues before CI does:

```bash
ruff check django_angular3 tests
ruff format --check django_angular3 tests
python -m unittest discover -s tests -p 'test*.py'
python -m sphinx docs docs/_build/html -W --keep-going
```

The documentation build uses the `docs` extra installed during contributor
setup. `-W` treats warnings as errors, matching CI.

## Releasing

The full release process — version bumping, tagging, building, and publishing
to PyPI via GitHub Actions — is documented in [doc/RELEASING.md](doc/RELEASING.md).

## Making solution-wide (multi-repository) changes

When a feature, refactoring, or architectural change spans multiple repositories
in the solution ecosystem (`openui-spec`, `angular-django2`, and `django-angular3`),
changes must be planned and executed in a strict upstream-to-downstream sequence.
Downstream packages must only consume published, verified upstream releases.

Follow this generic multi-stage workflow:

### Stage 0: Baseline pre-validation gate

Before making changes in any repository:

1. **Verify working tree cleanliness**: Ensure `main` is checked out, up to
   date with `origin/main`, and `git status` reports a clean working tree across
   all participating repositories.
2. **Run baseline test suites**: Execute the existing test suite and linters in
   each repository to confirm a clean starting state:
   - Specification repository: spec converters, schema validators, contract tests.
   - Frontend library repository: `npm run format:check`, `npm run lint`, `npm run test:ci`.
   - Backend package repository: `ruff check`, `ruff format --check`, `python -m unittest discover`.
3. Do not proceed if any repository has failing tests or uncommitted changes.

### Stage 1: Upstream specification layer (`openui-spec`)

The specification repository is the single source of truth for UI contracts
and schemas:

1. **Update contracts and schemas**: Apply additions, modifications, or
   deprecations to specification scopes, schemas, and canonical examples.
2. **Prune obsolete artifacts**: Remove deprecated designs, schemas, or
   reference files.
3. **Validate the specification**:
   - Run spec converters and contract validation suites.
   - Build documentation locally to verify link consistency and formatting.
4. **Commit, tag, and publish**: Commit the changes, tag the release if
   versioned, push to `origin/main`, and ensure the published spec artifact is
   available for downstream consumers.

### Stage 2: Frontend library layer (`angular-django2`)

The frontend library implements the schematics and Angular code generators
defined by the specification:

1. **Consume upstream contracts**: Align schematics, generators, and models with
   the updated specification.
2. **Implement library changes**: Add, modify, or retire schematics, templates,
   options, and utilities.
3. **Update tests and documentation**:
   - Update unit, schema-alias, and end-to-end integration test suites.
   - Update the reference application and CLI documentation.
4. **Run the validation gate**:
   - Code formatting: `npm run format:check`
   - Linting: `npm run lint`
   - Test suites: `npm run test:ci` and end-to-end checks
   - Package contents: `npm run pack:dry-run`
5. **Release and publish**:
   - Bump the package version via the documented versioning script.
   - Commit, tag with an annotated tag, and push to `origin/main --follow-tags`.
   - Publish the package to npm (via GitHub Actions publish workflow or local publish).
   - **Verification gate**: Verify the package is live on npm
     (`npm view <pkg> version`) and that hosted documentation (e.g. ReadTheDocs)
     has updated.

### Stage 3: Backend integration & orchestration layer (`django-angular3`)

The backend package provides Django integration, CLI wrappers, schema
validators, and automation skills that orchestrate the frontend tooling:

1. **Consume upstream library**: Update the pinned upstream package dependency
   or configuration (e.g., `ngAddPackage` in tool configuration). When you change
   the `angular-django2` pin, regenerate the command-mapping test fixture from that
   version with
   `python tests/fixtures/ngdj/sync_command_mapping.py <angular-django2>/projects/angular-django2`
   (never edit it by hand) and read the mapping's operation statuses: what `build_app`
   supports and refuses follows them (`docs/commands.md`, "Changes `build_app` turns into steps").
2. **Update commands and wrappers**:
   - Update argument parsers, execution builders, and
     management commands.
   - Update or retire CLI commands and options to match the upstream library's
     public interface.
3. **Update agent skills and workflows**: Update any skill definitions or
   orchestration workflows to use the new atomic primitives.
4. **Update tests and documentation**:
   - Update scenario fixtures, integration contracts, and unit tests.
   - Update command tables, narrative documentation, and architecture references.
5. **Run the validation gate**:
   - `ruff check django_angular3 tests docs`
   - `ruff format --check django_angular3 tests docs`
   - `python -m unittest discover -s tests -p 'test*.py'`
   - Sphinx documentation build: `python -m sphinx docs docs/_build/html -W --keep-going`
   - ngdj contract and fixture-drift tests. They read the `angular-django2` source, so
     the default run skips them unless that repository is checked out next to this one.
     Run them against the pinned release with
     `ANGULAR_DJANGO2_ROOT=<angular-django2 checkout> DJNG_REQUIRE_NGDJ=1 python -m unittest tests.test_ngdj_requirements tests.test_ngdj_command_mapping -v`
     (`ANGULAR_DJANGO2_ROOT` defaults to the sibling `../angular-django2`; with
     `DJNG_REQUIRE_NGDJ=1` a missing source or a sibling of another version fails instead of
     skipping). The CI job `ngdj-contract` does the same against the tag that
     `tool.ngAddPackage` pins, so bumping the pin fails that job until
     `tests/fixtures/ngdj/sync_command_mapping.py` has been run (step 1).
6. **Release and publish**:
   - Bump the version across `pyproject.toml`, package `__init__.py`, and `docs/conf.py`.
   - Commit, tag with an annotated tag, and push to `origin/main --follow-tags`.
   - Create the GitHub release to trigger the PyPI deployment workflow.
   - **Verification gate**: Verify the new version is live on PyPI
     (`pip index versions <pkg>`) and hosted documentation has updated.

### Stage 4: Cross-repository integration & cleanliness audit

Once all participating repositories have published their releases:

1. **End-to-end integration check**: Run an end-to-end smoke test or dry-run
   verifying that the orchestration workflow successfully coordinates across the
   stack.
2. **Solution-wide cleanliness audit**: Run `git status` across all workspaces
   to confirm no untracked artifacts, temporary files, or uncommitted edits remain.
