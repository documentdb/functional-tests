"""Tests for collation with partial filter expression indexes."""

from __future__ import annotations

import pytest
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import DUPLICATE_KEY_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Partial Index Filter Uses Index Collation]: the
# partialFilterExpression of an index uses the index's collation for its
# comparisons, so documents matching under collation are indexed while others
# are not.
COLLATION_PARTIAL_INDEX_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "partial_filter_case_insensitive_indexes_variant",
        indexes=[
            IndexModel(
                [("x", 1)],
                unique=True,
                collation={"locale": "en", "strength": 2},
                partialFilterExpression={"status": "active"},
                name="x_partial_ci",
            )
        ],
        docs=[
            {"_id": 1, "x": "apple", "status": "Active"},
            {"_id": 2, "x": "banana", "status": "inactive"},
        ],
        command=lambda ctx: {
            "insert": ctx.collection,
            "documents": [{"_id": 3, "x": "apple", "status": "ACTIVE"}],
        },
        error_code=DUPLICATE_KEY_ERROR,
        msg="partial index with collation should match filter case-insensitively",
    ),
    CommandTestCase(
        "partial_filter_excludes_non_matching",
        indexes=[
            IndexModel(
                [("x", 1)],
                unique=True,
                collation={"locale": "en", "strength": 2},
                partialFilterExpression={"status": "active"},
                name="x_partial_ci",
            )
        ],
        docs=[
            {"_id": 1, "x": "apple", "status": "active"},
            {"_id": 2, "x": "apple", "status": "inactive"},
        ],
        command=lambda ctx: {
            "insert": ctx.collection,
            "documents": [{"_id": 3, "x": "apple", "status": "archived"}],
        },
        expected={"ok": 1.0, "n": 1},
        msg="partial index should allow duplicate x when status does not match filter",
    ),
    CommandTestCase(
        "partial_filter_query_with_matching_collation",
        indexes=[
            IndexModel(
                [("x", 1)],
                collation={"locale": "en", "strength": 2},
                partialFilterExpression={"status": "active"},
                name="x_partial_ci",
            )
        ],
        docs=[
            {"_id": 1, "x": "apple", "status": "Active"},
            {"_id": 2, "x": "banana", "status": "Active"},
            {"_id": 3, "x": "apple", "status": "inactive"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": "APPLE", "status": "active"},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "x": "apple", "status": "Active"}],
        msg="find with matching collation should use partial index for case-insensitive match",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COLLATION_PARTIAL_INDEX_TESTS))
def test_collation_index_partial(database_client, collection, test):
    """Test collation with partial filter expression indexes."""
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
