"""Serve the built Angular application from Django on a single origin.

The generated ``index.html`` declares ``<base href="/">`` and the generated client calls
relative ``/api/...`` paths, so the browser files that ``ng_build`` leaves are served
from the root of the same origin as the API: no proxy and no CORS configuration are
needed.

Add the patterns last in the project's ``urls.py``, so that Django's own routes win::

    from django_angular3.spa import angular_urlpatterns

    urlpatterns = [
        path("admin/", admin.site.urls),
        path("api/v1/", include(router.urls)),
        *angular_urlpatterns(),
    ]

Nothing is set in the Django settings. The directory is configuration, found from
``settings.BASE_DIR`` like every other command: the workspace is
``artifacts.angularWorkspace`` of ``django-angular3-<project>.json`` and the rest is the
mandatory ``angular.build.browserOutputPath`` of ``django-angular3.json``, which sits
next to it.

The view reads the files through Django. That suits development, tests and small
deployments; behind real traffic, serve the same directory with a reverse proxy or a
static-file layer such as WhiteNoise and keep Django for ``/api/`` and ``/admin/``
(``doc/specifications/SPECIFICATIONS.md`` section 5.1 allows either).
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.http import Http404, HttpRequest, HttpResponseBase
from django.urls import URLPattern, re_path
from django.views.decorators.http import require_http_methods
from django.views.static import serve

from .angular import angular_browser_output_dir
from .config import ConfigError, load_project_config
from .settings import (
    DEFAULT_ANGULAR_SETTINGS,
    AngularCommandError,
    load_angular_settings,
)

DEFAULT_RESERVED_PREFIXES: tuple[str, ...] = (
    "api/",
    "api-auth/",
    "admin/",
    "static/",
)
"""Paths that belong to Django: when no route matched them, the answer is a 404."""


def _browser_output_dir() -> Path:
    """The existing browser output directory, or what is missing from the setup."""
    try:
        config = load_project_config()
        tool_config = (
            config.config_path.parent / DEFAULT_ANGULAR_SETTINGS["config_path"]
        )
        settings = load_angular_settings(config_path=tool_config)
    except (ConfigError, AngularCommandError, RuntimeError) as exc:
        raise ImproperlyConfigured(
            f"The Angular browser output directory cannot be calculated: {exc}"
        ) from exc

    root = angular_browser_output_dir(config, settings).resolve()
    if not root.is_dir():
        raise ImproperlyConfigured(
            f"The Angular browser output directory {root} does not exist. "
            "Build the application with `manage.py ng_build`."
        )
    if not (root / "index.html").is_file():
        raise ImproperlyConfigured(
            f"{root} has no index.html. Build the application with "
            "`manage.py ng_build`."
        )
    return root


def angular_urlpatterns(
    reserved: Sequence[str] = DEFAULT_RESERVED_PREFIXES,
) -> list[URLPattern]:
    """Return the catch-all pattern that serves the Angular browser output.

    The directory is calculated from the configuration files (see the module
    docstring) on each request, so a build made after the server started is picked up.
    A request is answered by

    1. the file of that name in the directory (``main-*.js``, ``styles-*.css``, ...);
    2. a 404 when the path starts with one of ``reserved`` (a wrong API URL must not
       answer with HTML) or names a file that is not in the directory (a stale hash
       must not answer with HTML either);
    3. ``index.html`` otherwise, so that a hard refresh on an Angular route works.
    """
    reserved_prefixes = tuple(reserved)

    @require_http_methods(["GET", "HEAD"])
    def angular_app(request: HttpRequest, path: str) -> HttpResponseBase:
        root = _browser_output_dir()
        if path.startswith(reserved_prefixes):
            raise Http404(f"No Django route matches /{path}")
        if path:
            candidate = (root / path).resolve()
            if not candidate.is_relative_to(root):
                raise Http404("Outside the Angular browser output")
            if candidate.is_file():
                return serve(request, path, document_root=root)
            if "." in candidate.name:
                raise Http404(f"{path} is not in the Angular browser output")
        return serve(request, "index.html", document_root=root)

    return [re_path(r"^(?P<path>.*)$", angular_app)]
