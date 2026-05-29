"""Tests for count command core behavior and null handling."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Success Response Structure]: a successful count returns exactly
# two fields: n (int32) and ok (double 1.0).
COUNT_SUCCESS_RESPONSE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "success_basic",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection},
        expected={"n": 1, "ok": 1.0},
        msg="count should return exactly n and ok fields",
    ),
]

# Property [Core Behavior]: count returns the number of documents matching
# the query, or all documents when no query is specified.
COUNT_CORE_BEHAVIOR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "core_nonexistent_collection",
        docs=None,
        command=lambda ctx: {"count": ctx.collection},
        expected={"n": 0, "ok": 1.0},
        msg="count on non-existent collection should return n=0",
    ),
    CommandTestCase(
        "core_empty_collection",
        docs=[],
        command=lambda ctx: {"count": ctx.collection},
        expected={"n": 0, "ok": 1.0},
        msg="count on empty collection should return n=0",
    ),
    CommandTestCase(
        "core_no_query",
        docs=[{"_id": 1}, {"_id": 2}, {"_id": 3}, {"_id": 4}, {"_id": 5}],
        command=lambda ctx: {"count": ctx.collection},
        expected={"n": 5, "ok": 1.0},
        msg="count without query should return total document count",
    ),
    CommandTestCase(
        "core_with_query",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}, {"_id": 3, "x": 1}],
        command=lambda ctx: {"count": ctx.collection, "query": {"x": 1}},
        expected={"n": 2, "ok": 1.0},
        msg="count with query should return only matching document count",
    ),
    CommandTestCase(
        "core_query_no_matches",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        command=lambda ctx: {"count": ctx.collection, "query": {"x": 99}},
        expected={"n": 0, "ok": 1.0},
        msg="count with non-matching query should return n=0",
    ),
    CommandTestCase(
        "core_case_sensitive_name",
        docs=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        command=lambda ctx: {"count": ctx.collection.upper()},
        expected={"n": 0, "ok": 1.0},
        msg="count is case-sensitive for collection names",
    ),
]

# Property [Null Success]: null-valued optional fields are treated as omitted.
COUNT_NULL_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "null_query",
        docs=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        command=lambda ctx: {"count": ctx.collection, "query": None},
        expected={"n": 3, "ok": 1.0},
        msg="count with query=null should return full document count",
    ),
    CommandTestCase(
        "null_skip",
        docs=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        command=lambda ctx: {"count": ctx.collection, "skip": None},
        expected={"n": 3, "ok": 1.0},
        msg="count with skip=null should treat it as skip=0",
    ),
    CommandTestCase(
        "null_read_concern",
        docs=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        command=lambda ctx: {"count": ctx.collection, "readConcern": None},
        expected={"n": 3, "ok": 1.0},
        msg="count with readConcern=null should use default read concern",
    ),
    CommandTestCase(
        "null_collation",
        docs=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        command=lambda ctx: {"count": ctx.collection, "collation": None},
        expected={"n": 3, "ok": 1.0},
        msg="count with collation=null should use default comparison",
    ),
    CommandTestCase(
        "null_max_time_ms",
        docs=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        command=lambda ctx: {"count": ctx.collection, "maxTimeMS": None},
        expected={"n": 3, "ok": 1.0},
        msg="count with maxTimeMS=null should be unbounded",
    ),
]

# Property [Null Error]: some fields reject null rather than treating it as
# omitted.
COUNT_NULL_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "null_limit",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "limit": None},
        error_code=BAD_VALUE_ERROR,
        msg="count with limit=null should produce an error",
    ),
]

COUNT_NULL_TESTS = COUNT_NULL_SUCCESS_TESTS + COUNT_NULL_ERROR_TESTS


COUNT_CORE_TESTS: list[CommandTestCase] = (
    COUNT_SUCCESS_RESPONSE_TESTS + COUNT_CORE_BEHAVIOR_TESTS + COUNT_NULL_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COUNT_CORE_TESTS))
def test_count_core(database_client, collection, test):
    """Test count command core behavior."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
