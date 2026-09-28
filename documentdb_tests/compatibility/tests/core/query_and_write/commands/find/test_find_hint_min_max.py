"""Tests for find command hint, min, and max fields."""

from __future__ import annotations

import pytest
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Hint and Min/Max]: find accepts hint as index name or key pattern,
# and min/max define inclusive/exclusive bounds when paired with hint.
FIND_HINT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "hint_index_name",
        docs=[{"_id": 1, "a": 10}, {"_id": 2, "a": 20}],
        indexes=[IndexModel("a")],
        command=lambda ctx: {"find": ctx.collection, "filter": {"a": 10}, "hint": "a_1"},
        expected=[{"_id": 1, "a": 10}],
        msg="find should accept hint with valid index name.",
    ),
    CommandTestCase(
        "hint_key_pattern",
        docs=[{"_id": 1, "a": 10}, {"_id": 2, "a": 20}],
        indexes=[IndexModel("a")],
        command=lambda ctx: {"find": ctx.collection, "filter": {"a": 10}, "hint": {"a": 1}},
        expected=[{"_id": 1, "a": 10}],
        msg="find should accept hint with valid key pattern document.",
    ),
    CommandTestCase(
        "hint_id_index",
        docs=[{"_id": 1, "a": 10}, {"_id": 2, "a": 20}],
        command=lambda ctx: {"find": ctx.collection, "filter": {"_id": 1}, "hint": "_id_"},
        expected=[{"_id": 1, "a": 10}],
        msg="find should accept hint with _id_ index name.",
    ),
    CommandTestCase(
        "hint_nonexistent_error",
        docs=[{"_id": 1, "a": 10}],
        command=lambda ctx: {"find": ctx.collection, "hint": "nonexistent_index"},
        error_code=BAD_VALUE_ERROR,
        msg="find should reject hint for non-existent index.",
    ),
    CommandTestCase(
        "min_with_hint",
        docs=[{"_id": i, "a": i * 10} for i in range(1, 6)],
        indexes=[IndexModel("a")],
        command=lambda ctx: {
            "find": ctx.collection,
            "min": {"a": 30},
            "hint": {"a": 1},
            "sort": {"a": 1},
        },
        expected=[{"_id": 3, "a": 30}, {"_id": 4, "a": 40}, {"_id": 5, "a": 50}],
        msg="find should return docs >= min bound with hint.",
    ),
    CommandTestCase(
        "max_with_hint",
        docs=[{"_id": i, "a": i * 10} for i in range(1, 6)],
        indexes=[IndexModel("a")],
        command=lambda ctx: {
            "find": ctx.collection,
            "max": {"a": 30},
            "hint": {"a": 1},
            "sort": {"a": 1},
        },
        expected=[{"_id": 1, "a": 10}, {"_id": 2, "a": 20}],
        msg="find should return docs < max bound (exclusive) with hint.",
    ),
    CommandTestCase(
        "min_max_range",
        docs=[{"_id": i, "a": i * 10} for i in range(1, 6)],
        indexes=[IndexModel("a")],
        command=lambda ctx: {
            "find": ctx.collection,
            "min": {"a": 20},
            "max": {"a": 40},
            "hint": {"a": 1},
            "sort": {"a": 1},
        },
        expected=[{"_id": 2, "a": 20}, {"_id": 3, "a": 30}],
        msg="find should return docs in [min, max) range with hint.",
    ),
    CommandTestCase(
        "returnkey_true_with_index",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        indexes=[IndexModel("a")],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"a": 10},
            "hint": "a_1",
            "returnKey": True,
        },
        expected=[{"a": 10}],
        msg="find should return only index key fields with returnKey=true.",
    ),
    CommandTestCase(
        "returnkey_true_no_index",
        docs=[{"_id": 1, "a": 10}],
        command=lambda ctx: {"find": ctx.collection, "returnKey": True},
        expected=[{}],
        msg="find should return empty documents with returnKey=true and no index hint.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIND_HINT_TESTS))
def test_find_hint(database_client, collection, test):
    """Test find command hint, min, and max behavior."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
