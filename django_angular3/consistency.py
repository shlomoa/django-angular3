"""Cross-input consistency: OpenUI bindings against the OpenAPI contract.

The ngdj commands bind an OpenUI element to the generated API client with two
attributes whose value is an unquoted expression ``<artifact>#<Symbol>``:

- ``uses.data`` = ``<apiPath>#<ApiService>`` (the ``data-service`` command);
- ``behaves.submit`` = ``<artifact>#<Symbol>.<method>`` (the ``reactive-form``
  command), where ``<Symbol>`` is a generated service and ``<method>`` one of its
  operations.

The reference index resolves each of them to the OpenAPI operations through the
resource identity rule (``resource_identity``): a service is the class of an
OpenAPI tag and a method is the camel-cased ``operationId``, as ``ng-openapi-gen``
names them. A value without ``#`` (``orders``, ``onSubmit(form.value)``) is not a
reference to a generated symbol and is not checked.
"""

from __future__ import annotations

import re
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import Any, Final

from .resource_identity import UNTAGGED, ResourceIdentityError, service_class_name

BINDING_ATTRIBUTES: Final = ("uses.data", "behaves.submit")
_HTTP_METHODS: Final = (
    "get",
    "put",
    "post",
    "delete",
    "options",
    "head",
    "patch",
    "trace",
)


@dataclass(frozen=True)
class ApiOperation:
    """One OpenAPI operation as the generated client exposes it."""

    service: str
    method: str
    http_method: str
    path: str
    operation_id: str


@dataclass(frozen=True)
class ApiReference:
    """One binding of an OpenUI element to a generated API symbol."""

    node_id: str
    attribute: str
    artifact: str
    service: str
    method: str | None


@dataclass(frozen=True)
class ReferenceIndex:
    """The references of an OpenUI document and the operations each resolves to."""

    references: tuple[ApiReference, ...]
    operations: Mapping[str, tuple[ApiOperation, ...]]
    errors: tuple[str, ...]

    def operations_of(self, node_id: str) -> tuple[ApiOperation, ...]:
        """The OpenAPI operations an OpenUI node depends on (for impact analysis)."""
        return self.operations.get(node_id, ())


def method_name(operation_id: str) -> str:
    """The method ``ng-openapi-gen`` generates for an ``operationId``."""
    parts = [part for part in re.split(r"[^A-Za-z0-9]+", operation_id) if part]
    if not parts:
        return ""
    return (
        parts[0][:1].lower()
        + parts[0][1:]
        + "".join(part[:1].upper() + part[1:] for part in parts[1:])
    )


def api_operations(
    openapi: Mapping[str, Any], suffix: str = "ApiService"
) -> dict[str, dict[str, ApiOperation]]:
    """The generated services of a contract: class -> method -> operation.

    An operation joins the service of each of its tags (the generator emits it into
    each), or ``api`` when it has none. An operation without ``operationId`` has no
    stable method name and is left out, as are tags the identity rule cannot name.
    """
    services: dict[str, dict[str, ApiOperation]] = {}
    paths = openapi.get("paths")
    for path, item in paths.items() if isinstance(paths, Mapping) else ():
        for http_method, operation in item.items() if isinstance(item, Mapping) else ():
            if http_method not in _HTTP_METHODS or not isinstance(operation, Mapping):
                continue
            operation_id = operation.get("operationId")
            tags = operation.get("tags")
            for tag in tags if isinstance(tags, list) and tags else [UNTAGGED]:
                try:
                    service = service_class_name(str(tag), suffix)
                except ResourceIdentityError:
                    continue
                method = (
                    method_name(operation_id) if isinstance(operation_id, str) else ""
                )
                if method:
                    services.setdefault(service, {})[method] = ApiOperation(
                        service, method, http_method, str(path), str(operation_id)
                    )
                else:
                    services.setdefault(service, {})
    return services


def extract_references(openui: Mapping[str, Any]) -> tuple[ApiReference, ...]:
    """The ``uses.data`` and ``behaves.submit`` bindings naming an artifact symbol."""
    return tuple(_references(openui))


def _references(node: Mapping[str, Any]) -> Iterator[ApiReference]:
    attrs = node.get("attrs")
    for attribute in BINDING_ATTRIBUTES:
        value = attrs.get(attribute) if isinstance(attrs, Mapping) else None
        if not isinstance(value, str) or "#" not in value:
            continue
        artifact, _, symbol = value.partition("#")
        service, _, method = symbol.partition(".")
        yield ApiReference(
            str(node.get("id")), attribute, artifact, service, method or None
        )
    for child in node.get("children") or ():
        if isinstance(child, Mapping):
            yield from _references(child)


def reference_index(
    openui: Mapping[str, Any],
    openapi: Mapping[str, Any],
    suffix: str = "ApiService",
) -> ReferenceIndex:
    """Resolve every reference of an OpenUI document against the OpenAPI contract."""
    services = api_operations(openapi, suffix)
    references = extract_references(openui)
    operations: dict[str, tuple[ApiOperation, ...]] = {}
    errors: list[str] = []
    for reference in references:
        methods = services.get(reference.service)
        where = f"OpenUI node '{reference.node_id}', {reference.attribute}"
        if methods is None:
            errors.append(
                f"{where}: the service {reference.service} is not generated from "
                "the OpenAPI contract (no tag gives that class)."
            )
            continue
        if reference.method is None:
            resolved = tuple(methods.values())
        elif reference.method in methods:
            resolved = (methods[reference.method],)
        else:
            errors.append(
                f"{where}: the operation {reference.service}.{reference.method} "
                "is not in the OpenAPI contract."
            )
            continue
        operations[reference.node_id] = operations.get(reference.node_id, ()) + resolved
    return ReferenceIndex(references, operations, tuple(errors))
