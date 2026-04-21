# Contributing

## Development setup

Install the project from source:

```bash
python -m pip install -e .
```

If you want YAML support for OpenAPI or UI definition files:

```bash
python -m pip install -e .[yaml]
```

## Local validation and build checks

The current scaffold is Python-only. Use the bundled project config to validate
the example inputs and generate a build plan locally:

```bash
python -m django_angular3.cli validate-project django-angular3.json
python -m django_angular3.cli build django-angular3.json --dry-run
python -m django_angular3.cli build django-angular3.json --output build
```

The bundled project config targets generated Angular artifacts under
`build/angular/` by default. No checked-in Angular package is required.

## Tests

Run the existing test suite with explicit discovery:

```bash
python -m unittest discover -s tests -p 'test*.py'
```

## CI/CD

This repository does not currently include checked-in CI/CD workflow files.
Until that changes, contributors should run the local validation and test
commands above before opening a pull request.
