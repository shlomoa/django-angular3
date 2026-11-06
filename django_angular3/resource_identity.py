"""The resource identity rule: OpenAPI tag, ngdj resource name and OpenUI binding.

A resource is an OpenAPI tag. ``ng-openapi-gen`` groups the operations of a tag in
one service class, named ``<PascalCase(tag)><serviceSuffix>``; the ngdj
``data-service`` schematic takes the tag as its resource name and wraps that class;
and an OpenUI ``uses.data`` binding names it as ``<apiPath>#<ApiService>``. The tag is
therefore the single key that joins the three, and the rule is recorded in
``doc/contracts/CHANGE_MODEL_CONTRACTS.md`` §2.2.1.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

_HTTP_METHODS: Final = frozenset(
    {"get", "put", "post", "delete", "options", "head", "patch", "trace"}
)
# The tags for which the generator's class name and the ngdj ``classify`` agree.
_TAG: Final = re.compile(r"^[A-Za-z][A-Za-z0-9]*(-[A-Za-z0-9]+)*$")


UNTAGGED: Final = "api"


class ResourceIdentityError(ValueError):
    """Raised when an OpenAPI subject has no single, nameable resource."""


class SubjectNotInDocument(ResourceIdentityError):
    """Raised when the path of a subject is not in the OpenAPI document."""


@dataclass(frozen=True)
class ResourceIdentity:
    """The resource of an OpenAPI subject: its tag, the ngdj name and the class."""

    tag: str
    resource: str
    api_service: str


def service_class_name(tag: str, suffix: str) -> str:
    """The class ``ng-openapi-gen`` generates for a tag: ``V1`` + ``ApiService``."""
    if not _TAG.match(tag):
        raise ResourceIdentityError(
            f"The OpenAPI tag {tag!r} is not a name the generated service class and "
            "the ngdj resource name agree on; use letters and digits, optionally "
            "joined by hyphens, starting with a letter."
        )
    return "".join(part[:1].upper() + part[1:] for part in tag.split("-")) + suffix


def binding_service(binding: str) -> str:
    """The ``<ApiService>`` of an OpenUI binding ``<apiPath>#<ApiService>``."""
    api_path, separator, api_service = binding.partition("#")
    if not separator or not api_path or not api_service:
        raise ResourceIdentityError(
            f"The binding {binding!r} is not <apiPath>#<ApiService>."
        )
    return api_service


def resource_identity(
    subject: str, document: Mapping[str, object], suffix: str = "ApiService"
) -> ResourceIdentity:
    """The resource of a ``path:`` or ``operation:`` Change subject.

    The tag comes from the document that holds the path (the candidate for a create).
    The subject must lead to exactly one tag. An untagged operation is in the tag
    ``api`` (the generator's default, class ``ApiApiService``). An operation with
    several tags is generated into each of their services, so it names no one.
    """
    kind, _, value = subject.partition(":")
    if kind == "path":
        path, operations = value, None
    elif kind == "operation":
        method, _, path = value.partition(" ")
        operations = {method.lower()}
    else:
        raise ResourceIdentityError(f"{subject} is not a path or operation subject.")
    paths = document.get("paths")
    item = paths.get(path) if isinstance(paths, Mapping) else None
    if not isinstance(item, Mapping):
        raise SubjectNotInDocument(f"{subject} is not in the OpenAPI document.")

    tags: set[str] = set()
    for method, operation in item.items():
        if method not in _HTTP_METHODS or not isinstance(operation, Mapping):
            continue
        if operations is not None and method not in operations:
            continue
        operation_tags = operation.get("tags")
        if not isinstance(operation_tags, list) or not operation_tags:
            # ng-openapi-gen puts an untagged operation in the tag ``Api``.
            tags.add(UNTAGGED)
            continue
        if len(operation_tags) > 1:
            raise ResourceIdentityError(
                f"{method.upper()} {path} has several tags "
                f"({', '.join(map(str, operation_tags))}); a resource needs one."
            )
        tags.add(str(operation_tags[0]))
    if len(tags) != 1:
        raise ResourceIdentityError(
            f"{subject} leads to {len(tags)} tags; a resource needs exactly one."
        )
    (tag,) = tags
    return ResourceIdentity(tag, tag, service_class_name(tag, suffix))
