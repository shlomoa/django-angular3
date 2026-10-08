"""Generate the committed fixtures of the end-to-end flow.

``fixtures/seed.json`` is the Django fixture of the tutorial project (25 customers, so
three pages at ``PAGE_SIZE = 10``, and 12 products) and ``fixtures/customers.openui.json``
is the OpenUI document the generated application is built from. Both are generated,
never edited by hand::

    python -m tests.e2e.generate_fixtures

``tests/test_e2e_fixtures.py`` fails when a committed file differs from this output.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FIXTURES = Path(__file__).resolve().parent / "fixtures"

CUSTOMER_COUNT = 25
PRODUCT_COUNT = 12
PAGE_SIZE = 10

_FIRST_NAMES = (
    "Ada",
    "Brian",
    "Chloe",
    "Dmitri",
    "Elena",
    "Farid",
    "Grace",
    "Hugo",
    "Ines",
    "Jonas",
    "Keiko",
    "Liam",
    "Maya",
    "Noah",
    "Olga",
    "Pavel",
    "Quinn",
    "Rosa",
    "Samir",
    "Tara",
    "Umar",
    "Vera",
    "Wen",
    "Xavier",
    "Yara",
)
_LAST_NAMES = (
    "Aldridge",
    "Bianchi",
    "Castillo",
    "Dvorak",
    "Eriksen",
    "Fontaine",
    "Garcia",
    "Hoffmann",
    "Ivanova",
    "Jensen",
    "Kowalski",
    "Lindgren",
    "Moreau",
    "Nakamura",
    "Okafor",
    "Petrov",
    "Quintero",
    "Rossi",
    "Santos",
    "Tanaka",
    "Ulrich",
    "Varga",
    "Weber",
    "Xu",
    "Yilmaz",
)
_PRODUCTS = (
    "Anvil",
    "Bolt",
    "Clamp",
    "Drill",
    "Edger",
    "File",
    "Gauge",
    "Hammer",
    "Jack",
    "Knife",
    "Level",
    "Mallet",
)


def seed_documents() -> list[dict[str, Any]]:
    """The Django fixture: customers first, then products, with explicit keys."""
    documents: list[dict[str, Any]] = []
    for index in range(CUSTOMER_COUNT):
        first, last = _FIRST_NAMES[index], _LAST_NAMES[index]
        documents.append(
            {
                "model": "shop.customer",
                "pk": index + 1,
                "fields": {
                    "name": f"{first} {last}",
                    "email": f"{first}.{last}@example.com".lower(),
                    "phone": f"+1-555-01{index:02d}",
                    # The fifth of the customers is inactive.
                    "active": index % 5 != 4,
                },
            }
        )
    for index in range(PRODUCT_COUNT):
        documents.append(
            {
                "model": "shop.product",
                "pk": index + 1,
                "fields": {
                    "name": _PRODUCTS[index],
                    "price": round(4.5 + index * 2.25, 2),
                    "sku": f"SKU-{index + 1:04d}",
                },
            }
        )
    return documents


def _route(element_id: str, path: str, target: str, title: str) -> dict[str, Any]:
    return {
        "id": element_id,
        "type": "Route",
        "attrs": {
            "uses.path": json.dumps(path),
            "uses.target": json.dumps(target),
            "uses.title": json.dumps(title),
        },
    }


def _navigation_item(element_id: str, label: str, route: str) -> dict[str, Any]:
    return {
        "id": element_id,
        "type": "NavItem",
        "attrs": {"uses.label": json.dumps(label), "uses.route": json.dumps(route)},
    }


def _page(element_id: str, route: str, title: str) -> dict[str, Any]:
    return {
        "id": element_id,
        "type": "DashboardPage",
        "attrs": {"uses.route": json.dumps(route), "uses.title": json.dumps(title)},
    }


def openui_document() -> dict[str, Any]:
    """The application: routing, navigation, two pages and a paginated table.

    The root is the ``html`` element ngdj uses for documents that hold an
    ``Application`` next to its pages. A table cannot be composed into a page, so it is
    a sibling element that the host places in the customers page.
    """
    return {
        "id": "root",
        "version": "0.12.0",
        "type": "html",
        "children": [
            {
                "id": "crmApp",
                "type": "Application",
                "children": [
                    {
                        "id": "appRouting",
                        "type": "Routing",
                        "children": [
                            _route(
                                "customersRoute",
                                "customers",
                                "customersPage",
                                "Customers",
                            ),
                            _route(
                                "productsRoute",
                                "products",
                                "productsPage",
                                "Products",
                            ),
                        ],
                    },
                    {
                        "id": "appNavigation",
                        "type": "Navigation",
                        "attrs": {"uses.ariaLabel": json.dumps("Primary")},
                        "children": [
                            _navigation_item(
                                "customersNavigation", "Customers", "customersRoute"
                            ),
                            _navigation_item(
                                "productsNavigation", "Products", "productsRoute"
                            ),
                        ],
                    },
                ],
            },
            _page("customersPage", "customers", "Customers"),
            {
                "id": "customers",
                "type": "table",
                "attrs": {"behaves.paginate": "paginateCustomers($event)"},
                "children": [
                    {"id": "customersCaption", "type": "caption"},
                    {"id": "customersHeader", "type": "thead"},
                    {"id": "customersRow", "type": "tr"},
                ],
            },
            _page("productsPage", "products", "Products"),
        ],
    }


def _dump(document: object) -> str:
    return json.dumps(document, indent=2) + "\n"


def generated_files() -> dict[Path, str]:
    """Every generated fixture with its exact content."""
    return {
        FIXTURES / "seed.json": _dump(seed_documents()),
        FIXTURES / "customers.openui.json": _dump(openui_document()),
    }


def main() -> None:
    for path, content in generated_files().items():
        path.write_text(content, encoding="utf-8", newline="\n")
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
