"""Serve the built Angular application from Django on a single origin.

``ng_build`` leaves the browser bundle in ``<workspace>/dist/<app>/browser``. The
generated ``index.html`` declares ``<base href="/">`` and the generated client calls
relative ``/api/...`` paths, so the bundle is served from the root of the same origin as
the API: no proxy and no CORS configuration are needed.

Add the patterns last in the project's ``urls.py``, so that Django's own routes win::

    from django_angular3.spa import angular_urlpatterns

    urlpatterns = [
        path("admin/", admin.site.urls),
        path("api/v1/", include(router.urls)),
        *angular_urlpatterns(),
    ]

and point ``ANGULAR_DIST_DIR`` at the bundle in the project settings.

The view reads the files through Django. That suits development, tests and small
deployments; behind real traffic, serve the same directory with a reverse proxy or a
static-file layer such as WhiteNoise and keep Django for ``/api/`` and ``/admin/``
(``doc/specifications/SPECIFICATIONS.md`` section 5.1 allows either).
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import Http404, HttpRequest, HttpResponseBase
from django.urls import URLPattern, re_path
from django.views.decorators.http import require_http_methods
from django.views.static import serve

DEFAULT_RESERVED_PREFIXES: tuple[str, ...] = (
    "api/",
    "api-auth/",
    "admin/",
    "static/",
)
"""Paths that belong to Django: when no route matched them, the answer is a 404."""


def _resolve_dist_dir(dist_dir: str | Path | None) -> Path:
    """Return the existing bundle directory, or explain what is missing."""
    configured = dist_dir if dist_dir is not None else _setting()
    root = Path(configured).resolve()
    if not root.is_dir():
        raise ImproperlyConfigured(
            f"The Angular bundle directory {root} does not exist. "
            "Build the application with `manage.py ng_build` or correct "
            "ANGULAR_DIST_DIR."
        )
    if not (root / "index.html").is_file():
        raise ImproperlyConfigured(
            f"{root} has no index.html. Build the application with "
            "`manage.py ng_build` or point ANGULAR_DIST_DIR at dist/<app>/browser."
        )
    return root


def _setting() -> str | Path:
    configured = getattr(settings, "ANGULAR_DIST_DIR", None)
    if not configured:
        raise ImproperlyConfigured(
            "Set ANGULAR_DIST_DIR to the Angular bundle (dist/<app>/browser) or pass "
            "dist_dir to angular_urlpatterns()."
        )
    return configured


def angular_urlpatterns(
    dist_dir: str | Path | None = None,
    reserved: Sequence[str] = DEFAULT_RESERVED_PREFIXES,
) -> list[URLPattern]:
    """Return the catch-all pattern that serves the Angular bundle.

    ``dist_dir`` defaults to ``settings.ANGULAR_DIST_DIR`` and is read on each request,
    so a build made after the server started is picked up. A request is answered by

    1. the file of that name in the bundle (``main-*.js``, ``styles-*.css``, ...);
    2. a 404 when the path starts with one of ``reserved`` (a wrong API URL must not
       answer with HTML) or names a file that is not in the bundle (a stale hash must
       not answer with HTML either);
    3. ``index.html`` otherwise, so that a hard refresh on an Angular route works.
    """
    reserved_prefixes = tuple(reserved)

    @require_http_methods(["GET", "HEAD"])
    def angular_app(request: HttpRequest, path: str) -> HttpResponseBase:
        root = _resolve_dist_dir(dist_dir)
        if path.startswith(reserved_prefixes):
            raise Http404(f"No Django route matches /{path}")
        if path:
            candidate = (root / path).resolve()
            if not candidate.is_relative_to(root):
                raise Http404("Outside the Angular bundle")
            if candidate.is_file():
                return serve(request, path, document_root=root)
            if "." in candidate.name:
                raise Http404(f"{path} is not in the Angular bundle")
        return serve(request, "index.html", document_root=root)

    return [re_path(r"^(?P<path>.*)$", angular_app)]
