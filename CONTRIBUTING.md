# Contributing

## Assumptions

- You are running **Python 3.12 or later**. Check with `python --version`.
- You have **Git** installed and configured with your GitHub identity.
- You have cloned the repository and your working directory is the repo root.
- No Node.js, Angular CLI, or other frontend tooling is required to contribute
  to this repository. It is a Python-only package.

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

Then install the package with dev tooling:

```bash
python -m pip install -e .[dev]
```

## Development setup

Install the project from source with dev tooling already covered in
[Prerequisites](#prerequisites) above.

If you also want YAML support for OpenAPI or UI definition files:

```bash
python -m pip install -e .[dev,yaml]
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
- `deploy.yml` — builds and publishes the package to PyPI via Trusted
  Publishing when a GitHub Release is published.

Before opening a pull request, run linting and the test suite locally to
catch issues before CI does:

```bash
ruff check django_angular3 tests
ruff format django_angular3 tests
python -m unittest discover -s tests -p 'test*.py'
```

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
   or configuration (e.g., `ngAddPackage` in tool configuration).
2. **Update commands and wrappers**:
   - Update command allowlists, argument parsers, execution builders, and
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

