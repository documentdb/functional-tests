"""Tests for collation behavior with clustered collections."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import DUPLICATE_KEY_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import CustomCollection

# Property [Clustered Collection Collation]: a clustered collection can be
# created with a default collation, and collation affects filter matching and
# _id uniqueness enforcement.
COLLATION_CLUSTERED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "clustered_default_collation_filter",
        target_collection=CustomCollection(
            options={
                "clusteredIndex": {"key": {"_id": 1}, "unique": True},
                "collation": {"locale": "en", "strength": 2},
            }
        ),
        docs=[
            {"_id": "apple", "v": 1},
            {"_id": "banana", "v": 2},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"_id": "Apple"},
        },
        expected=[{"_id": "apple", "v": 1}],
        msg="clustered collection with default collation should use it for _id filter matching",
    ),
    CommandTestCase(
        "clustered_collation_rejects_case_variant_id",
        target_collection=CustomCollection(
            options={
                "clusteredIndex": {"key": {"_id": 1}, "unique": True},
                "collation": {"locale": "en", "strength": 2},
            }
        ),
        docs=[{"_id": "apple", "v": 1}],
        command=lambda ctx: {
            "insert": ctx.collection,
            "documents": [{"_id": "Apple", "v": 2}],
        },
        error_code=DUPLICATE_KEY_ERROR,
        msg="clustered collection with collation should reject case-variant _id as duplicate",
    ),
    CommandTestCase(
        "clustered_explicit_collation_filter",
        target_collection=CustomCollection(
            options={"clusteredIndex": {"key": {"_id": 1}, "unique": True}}
        ),
        docs=[
            {"_id": "apple", "v": 1},
            {"_id": "Apple", "v": 2},
            {"_id": "banana", "v": 3},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"_id": "apple"},
            "sort": {"_id": 1},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": "Apple", "v": 2},
            {"_id": "apple", "v": 1},
        ],
        msg="clustered collection should support explicit collation on find",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COLLATION_CLUSTERED_TESTS))
def test_collation_clustered(database_client, collection, test):
    """Test collation behavior with clustered collections."""
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
