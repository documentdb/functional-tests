"""Tests for find command core behavior and response structure."""

from __future__ import annotations

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertProperties, assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists, IsType

# Property [Primary Operation]: find returns matching documents from a collection,
# or all documents when no filter is specified.
FIND_CORE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "all_documents_no_filter",
        docs=[{"_id": 1, "a": 10}, {"_id": 2, "a": 20}, {"_id": 3, "a": 30}],
        command=lambda ctx: {"find": ctx.collection, "sort": {"_id": 1}},
        expected=[{"_id": 1, "a": 10}, {"_id": 2, "a": 20}, {"_id": 3, "a": 30}],
        msg="find should return all documents when no filter specified.",
    ),
    CommandTestCase(
        "filter_returns_matching",
        docs=[{"_id": 1, "a": 10}, {"_id": 2, "a": 20}, {"_id": 3, "a": 10}],
        command=lambda ctx: {"find": ctx.collection, "filter": {"a": 10}, "sort": {"_id": 1}},
        expected=[{"_id": 1, "a": 10}, {"_id": 3, "a": 10}],
        msg="find should return only documents matching the filter.",
    ),
    CommandTestCase(
        "empty_collection",
        docs=[],
        command=lambda ctx: {"find": ctx.collection},
        expected=[],
        msg="find should return empty result for empty collection.",
    ),
    CommandTestCase(
        "nonexistent_collection",
        docs=None,
        command=lambda ctx: {"find": ctx.collection},
        expected=[],
        msg="find should return empty result for non-existent collection.",
    ),
    CommandTestCase(
        "empty_filter_returns_all",
        docs=[{"_id": 1, "x": "a"}, {"_id": 2, "x": "b"}],
        command=lambda ctx: {"find": ctx.collection, "filter": {}, "sort": {"_id": 1}},
        expected=[{"_id": 1, "x": "a"}, {"_id": 2, "x": "b"}],
        msg="find should return all documents with empty filter.",
    ),
    CommandTestCase(
        "multiple_conditions_implicit_and",
        docs=[{"_id": 1, "a": 1, "b": 2}, {"_id": 2, "a": 1, "b": 3}],
        command=lambda ctx: {"find": ctx.collection, "filter": {"a": 1, "b": 2}},
        expected=[{"_id": 1, "a": 1, "b": 2}],
        msg="find should use implicit AND for multiple filter conditions.",
    ),
    CommandTestCase(
        "nested_field_dot_notation",
        docs=[{"_id": 1, "obj": {"x": 10}}, {"_id": 2, "obj": {"x": 20}}],
        command=lambda ctx: {"find": ctx.collection, "filter": {"obj.x": 10}},
        expected=[{"_id": 1, "obj": {"x": 10}}],
        msg="find should match nested fields using dot notation.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIND_CORE_TESTS))
def test_find_core_behavior(database_client, collection, test):
    """Test find command core behavior."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )


def test_find_response_structure(collection):
    """Test find response contains cursor with firstBatch, id, and ns fields."""
    collection.insert_one({"_id": 1, "a": 1})
    result = execute_command(collection, {"find": collection.name})
    assertResult(
        result,
        expected={
            "cursor.firstBatch": Exists(),
            "cursor.id": IsType("long"),
            "cursor.ns": IsType("string"),
        },
        raw_res=True,
        msg="find should return cursor with firstBatch, id, and ns.",
    )


def test_find_cursor_id_zero_when_exhausted(collection):
    """Test cursor id is 0 when all results fit in first batch."""
    collection.insert_many([{"_id": i} for i in range(3)])
    result = execute_command(collection, {"find": collection.name})
    assertProperties(
        result,
        {"cursor.id": Eq(Int64(0))},
        raw_res=True,
        msg="find should return cursor id 0 when all results returned.",
    )
