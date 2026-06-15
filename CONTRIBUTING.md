# Contributing

## Development setup

Install the project from source with dev tooling:

```bash
python -m pip install -e .[dev]
```

This installs `ruff` for linting and formatting. If you also want YAML support
for OpenAPI or UI definition files:

```bash
python -m pip install -e .[dev,yaml]
```

## Local validation and build checks

The current scaffold is Python-only. Use the bundled project config to validate
the example inputs and generate a build plan locally:

```bash
django-admin validate-project django-angular3.json
django-admin build django-angular3.json --dry-run
django-admin build django-angular3.json --output build
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
