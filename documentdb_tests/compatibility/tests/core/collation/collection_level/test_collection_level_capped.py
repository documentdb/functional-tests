"""Tests for collation behavior with capped collections."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import CappedCollection, CustomCollection

# Property [Capped Collection Collation]: a capped collection can be created
# with a default collation, and collation affects filter matching and sort
# ordering on capped collections the same as regular collections.
COLLATION_CAPPED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "capped_with_default_collation_filter",
        target_collection=CustomCollection(
            options={"capped": True, "size": 4096, "collation": {"locale": "en", "strength": 2}}
        ),
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": "apple"},
        },
        expected=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
        ],
        msg="capped collection with default collation should use it for filter matching",
    ),
    CommandTestCase(
        "capped_explicit_collation_filter",
        target_collection=CappedCollection(size=4096),
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": "apple"},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
        ],
        msg="capped collection should support explicit collation on find",
    ),
    CommandTestCase(
        "capped_collation_sort",
        target_collection=CappedCollection(size=4096),
        docs=[
            {"_id": 1, "x": "banana"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "cherry"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {},
            "sort": {"x": 1},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 2, "x": "Apple"},
            {"_id": 1, "x": "banana"},
            {"_id": 3, "x": "cherry"},
        ],
        msg="capped collection should support collation sort ordering",
    ),
    CommandTestCase(
        "capped_count_with_collation",
        target_collection=CappedCollection(size=4096),
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"x": "apple"},
            "collation": {"locale": "en", "strength": 2},
        },
        expected={"n": 2, "ok": 1.0},
        msg="count on capped collection should support collation",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COLLATION_CAPPED_TESTS))
def test_collation_capped(database_client, collection, test):
    """Test collation behavior with capped collections."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    expected = test.build_expected(ctx)
    assertResult(
        result,
        expected=expected,
        error_code=test.error_code,
        msg=test.msg,
        raw_res=not isinstance(expected, list),
    )
