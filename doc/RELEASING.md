# Releasing django-angular3

This document is the single source of truth for the release process of the
`django-angular3` Python package. Follow every stage in order; do not skip
stages or publish from a dirty or un-verified working tree.

---

## Assumptions

- You are running **Python 3.11 or later**. Check with `python --version`.
- **Git** is installed and your local `main` is up to date with `origin/main`.
- You have already completed the normal contributor workflow (all tests pass,
  all linting is clean) on the commit you intend to release.
- The GitHub repository is configured for **PyPI Trusted Publishing**: the
  `deploy.yml` workflow is authorised to publish to PyPI via OIDC — no API
  tokens or stored credentials are required.

---

## Prerequisites

These are one-time or per-environment setup steps. If you have already done
them in your current environment you can skip to stage 1.

**System tools**

- Python 3.11+ with `pip`
- Git with write access to `shlomoa/django-angular3` on GitHub
- A browser to create the GitHub release and monitor Actions

**Python environment**

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

python -m pip install --upgrade build
python -m pip install -e .[dev]    # ruff and other dev tooling
python -m pip install -e .[docs]   # Sphinx and doc dependencies
```

**GitHub / PyPI access**

- Write access to the `shlomoa/django-angular3` GitHub repository (to push
  tags and publish releases)
- The PyPI Trusted Publishing link is already configured — no further PyPI
  account setup is required for normal releases. The deploy workflow publishes
  from the GitHub Actions `pypi` environment; keep that environment aligned
  with the PyPI trusted publisher entry.

---

## 1. Verify the working tree

All release work starts from a clean `main` branch. Confirm:

```bash
git checkout main
git pull origin main
git status          # must report "nothing to commit, working tree clean"
```

If there are uncommitted changes, commit or stash them before continuing.

---

## 2. Run the full test suite

```bash
python -m unittest discover -s tests -p "test*.py"
```

All tests must pass. Do not proceed if any test fails.

---

## 3. Lint and format

Ruff is enforced by the `lint` job in `build.yml` on every push, so the
main branch should always be clean. Verify locally before tagging:

```bash
ruff check django_angular3 tests
ruff format --check django_angular3 tests
```

Fix any reported issues, commit, and re-run the test suite before continuing.

---

## 4. Build and verify documentation

```bash
cd docs
sphinx-build -b html . _build/html
```

Open `docs/_build/html/index.html` in a browser and verify that:
- the version shown matches the intended release version
- all API pages render without `[unknown]` or import errors

---

## 5. Bump the version

The version lives in `pyproject.toml`:

```toml
[project]
version = "X.Y.Z"
```

Version numbers follow [PEP 440](https://peps.python.org/pep-0440/) and
[Semantic Versioning](https://semver.org/) conventions:

| Release type | Example |
|---|---|
| Alpha pre-release | `0.2.0a1` |
| Beta pre-release | `0.2.0b1` |
| Release candidate | `0.2.0rc1` |
| Final release | `0.2.0` |
| Patch release | `0.2.1` |

Edit `pyproject.toml` and update the `version` field. Then commit:

```bash
git add pyproject.toml
git commit -m "chore: bump version to X.Y.Z"
```

---

## 6. Tag the release

Create an annotated tag with the version prefixed by `v`:

```bash
git tag -a vX.Y.Z -m "Release vX.Y.Z"
```

---

## 7. Build the distribution (optional local check)

The CI workflow builds the distribution automatically. If you want to verify
the build locally before pushing:

```bash
python -m build
```

This produces two artefacts in `dist/`:
- `django_angular3-X.Y.Z.tar.gz` (sdist)
- `django_angular3-X.Y.Z-py3-none-any.whl` (wheel)

---

## 8. Push the tag and commits

```bash
git push origin main
git push origin vX.Y.Z
```

---

## 9. Create a GitHub release and publish to PyPI

1. Go to <https://github.com/shlomoa/django-angular3/releases/new>.
2. Select the tag `vX.Y.Z`.
3. Set the title to `vX.Y.Z`.
4. Write a short release summary covering notable changes, breaking changes (if
   any), and upgrade instructions.
5. Click **Publish release**.

Publishing the release triggers `.github/workflows/deploy.yml`, which builds
the sdist and wheel and uploads them to PyPI using Trusted Publishing. No
manual upload step is required.

---

## Post-release

- Monitor the **Actions** tab on GitHub to confirm the `deploy.yml` run
  succeeded.
- Verify the new version appears on <https://pypi.org/project/django-angular3/>.
- Open a follow-up commit on `main` that bumps the version to the next
  development pre-release (e.g. `0.3.0a1`) so that `main` is never on a
  released version.

---

## Recovering from a failed release

| Problem | Action |
|---|---|
| Bad tag pushed, not yet published to PyPI | `git tag -d vX.Y.Z`, `git push origin :vX.Y.Z`, fix, re-tag |
| `deploy.yml` failed before upload | Re-run the workflow from the Actions tab, or delete the GitHub release, fix the issue, and re-publish |
| Bad upload to PyPI (yanked or wrong files) | Use the PyPI "yank" feature for the broken release; do **not** delete it. Publish a corrected patch version immediately. |
