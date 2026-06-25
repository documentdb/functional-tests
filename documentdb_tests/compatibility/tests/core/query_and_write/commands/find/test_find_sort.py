"""Tests for find command sort functionality."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    SORT_ORDER_RANGE_ERROR,
    SORT_ORDER_TYPE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Sort Ordering]: find applies ascending, descending, and compound sort
# correctly, and rejects invalid sort specifications.
FIND_SORT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "ascending",
        docs=[{"_id": 1, "a": 30}, {"_id": 2, "a": 10}, {"_id": 3, "a": 20}],
        command=lambda ctx: {"find": ctx.collection, "sort": {"a": 1}},
        expected=[{"_id": 2, "a": 10}, {"_id": 3, "a": 20}, {"_id": 1, "a": 30}],
        msg="find should sort ascending by field value.",
    ),
    CommandTestCase(
        "descending",
        docs=[{"_id": 1, "a": 30}, {"_id": 2, "a": 10}, {"_id": 3, "a": 20}],
        command=lambda ctx: {"find": ctx.collection, "sort": {"a": -1}},
        expected=[{"_id": 1, "a": 30}, {"_id": 3, "a": 20}, {"_id": 2, "a": 10}],
        msg="find should sort descending by field value.",
    ),
    CommandTestCase(
        "compound",
        docs=[
            {"_id": 1, "a": 1, "b": 30},
            {"_id": 2, "a": 1, "b": 10},
            {"_id": 3, "a": 2, "b": 20},
        ],
        command=lambda ctx: {"find": ctx.collection, "sort": {"a": 1, "b": -1}},
        expected=[
            {"_id": 1, "a": 1, "b": 30},
            {"_id": 2, "a": 1, "b": 10},
            {"_id": 3, "a": 2, "b": 20},
        ],
        msg="find should apply compound sort with tiebreaker.",
    ),
    CommandTestCase(
        "nested_field",
        docs=[
            {"_id": 1, "obj": {"x": 30}},
            {"_id": 2, "obj": {"x": 10}},
            {"_id": 3, "obj": {"x": 20}},
        ],
        command=lambda ctx: {"find": ctx.collection, "sort": {"obj.x": 1}},
        expected=[
            {"_id": 2, "obj": {"x": 10}},
            {"_id": 3, "obj": {"x": 20}},
            {"_id": 1, "obj": {"x": 30}},
        ],
        msg="find should sort on nested field via dot notation.",
    ),
    CommandTestCase(
        "value_zero_error",
        docs=[],
        command=lambda ctx: {"find": ctx.collection, "sort": {"a": 0}},
        error_code=SORT_ORDER_RANGE_ERROR,
        msg="find should reject sort value 0.",
    ),
    CommandTestCase(
        "value_two_error",
        docs=[],
        command=lambda ctx: {"find": ctx.collection, "sort": {"a": 2}},
        error_code=SORT_ORDER_RANGE_ERROR,
        msg="find should reject sort value 2.",
    ),
    CommandTestCase(
        "string_value_error",
        docs=[],
        command=lambda ctx: {"find": ctx.collection, "sort": {"a": "asc"}},
        error_code=SORT_ORDER_TYPE_ERROR,
        msg="find should reject string sort order value.",
    ),
    CommandTestCase(
        "empty_spec_accepted",
        docs=[{"_id": 1, "a": 10}, {"_id": 2, "a": 20}],
        command=lambda ctx: {"find": ctx.collection, "sort": {}},
        expected=[{"_id": 1, "a": 10}, {"_id": 2, "a": 20}],
        msg="find should accept empty sort specification.",
    ),
    CommandTestCase(
        "bson_type_ordering_wiring",
        docs=[{"_id": 1, "a": "hello"}, {"_id": 2, "a": 42}, {"_id": 3, "a": None}],
        command=lambda ctx: {"find": ctx.collection, "sort": {"a": 1}},
        expected=[
            {"_id": 3, "a": None},
            {"_id": 2, "a": 42},
            {"_id": 1, "a": "hello"},
        ],
        msg="find should sort mixed types by BSON comparison order.",
    ),
    CommandTestCase(
        "natural_order_insertion",
        docs=[{"_id": 3, "x": "c"}, {"_id": 1, "x": "a"}, {"_id": 2, "x": "b"}],
        command=lambda ctx: {"find": ctx.collection},
        expected=[{"_id": 3, "x": "c"}, {"_id": 1, "x": "a"}, {"_id": 2, "x": "b"}],
        msg="find should return documents in insertion order when no sort specified.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIND_SORT_TESTS))
def test_find_sort(database_client, collection, test):
    """Test find command sort behavior."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        ignore_doc_order=test.id == "empty_spec_accepted",
    )
