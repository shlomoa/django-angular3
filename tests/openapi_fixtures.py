"""Reusable valid OpenAPI documents for tests."""

from __future__ import annotations

from typing import Any


def valid_openapi_document() -> dict[str, Any]:
    """Return the smallest OpenAPI document accepted by all validators."""
    return {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {"/items/": {"get": {"responses": {"200": {"description": "ok"}}}}},
    }
