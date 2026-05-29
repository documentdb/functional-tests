"""Tests for $first accumulator null, missing, and edge case behavior."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Null and Missing NOT Excluded]: $first returns whatever the
# first document has, including null and missing values.
FIRST_NULL_MISSING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "null_first_then_value",
        docs=[{"_id": 1, "v": None}, {"_id": 2, "v": 5}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$first": "$v"}}},
        ],
        expected=[{"_id": None, "result": None}],
        msg="$first should return null when first doc has null (first wins)",
    ),
    AccumulatorTestCase(
        "null_missing_first_then_value",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "v": 5}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$first": "$v"}}},
        ],
        expected=[{"_id": None, "result": None}],
        msg="$first should return null when first doc has missing field",
    ),
    AccumulatorTestCase(
        "null_value_first_then_null",
        docs=[{"_id": 1, "v": 5}, {"_id": 2, "v": None}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$first": "$v"}}},
        ],
        expected=[{"_id": None, "result": 5}],
        msg="$first should return 5 when first doc has value, second is null",
    ),
    AccumulatorTestCase(
        "null_value_first_then_missing",
        docs=[{"_id": 1, "v": 5}, {"_id": 2, "x": 1}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$first": "$v"}}},
        ],
        expected=[{"_id": None, "result": 5}],
        msg="$first should return 5 when first doc has value, second is missing",
    ),
    AccumulatorTestCase(
        "null_all",
        docs=[{"_id": 1, "v": None}, {"_id": 2, "v": None}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$first": "$v"}}},
        ],
        expected=[{"_id": None, "result": None}],
        msg="$first should return null when all docs have null",
    ),
    AccumulatorTestCase(
        "null_missing_all",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$first": "$v"}}},
        ],
        expected=[{"_id": None, "result": None}],
        msg="$first should return null when all docs have missing field",
    ),
    AccumulatorTestCase(
        "null_and_missing_mixed",
        docs=[{"_id": 1, "v": None}, {"_id": 2, "x": 1}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$first": "$v"}}},
        ],
        expected=[{"_id": None, "result": None}],
        msg="$first should return null when first is null and second is missing",
    ),
]

# Property [Edge Cases]: edge cases unique to the accumulator context.
FIRST_EDGE_CASE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "edge_single_doc",
        docs=[{"v": 42}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": 42}],
        msg="$first of a single document should return that document's value",
    ),
    AccumulatorTestCase(
        "edge_single_null_doc",
        docs=[{"v": None}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": None}],
        msg="$first of a single null document should return null",
    ),
    AccumulatorTestCase(
        "edge_single_missing_doc",
        docs=[{"x": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": None}],
        msg="$first of a single document with missing field should return null",
    ),
    AccumulatorTestCase(
        "edge_array_not_traversed",
        docs=[{"_id": 1, "v": [5, 1, 8]}, {"_id": 2, "v": [3, 9, 2]}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$first": "$v"}}},
        ],
        expected=[{"_id": None, "result": [5, 1, 8]}],
        msg="$first should return array as whole value, not traverse it",
    ),
    AccumulatorTestCase(
        "edge_empty_collection",
        docs=[],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[],
        msg="$first on empty collection should produce no groups (empty result)",
    ),
    AccumulatorTestCase(
        "edge_order_dependent_asc",
        docs=[{"v": 3}, {"v": 1}, {"v": 5}, {"v": 2}, {"v": 4}],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$group": {"_id": None, "result": {"$first": "$v"}}},
        ],
        expected=[{"_id": None, "result": 1}],
        msg="$first with ascending sort should return smallest value",
    ),
    AccumulatorTestCase(
        "edge_order_dependent_desc",
        docs=[{"v": 3}, {"v": 1}, {"v": 5}, {"v": 2}, {"v": 4}],
        pipeline=[
            {"$sort": {"v": -1}},
            {"$group": {"_id": None, "result": {"$first": "$v"}}},
        ],
        expected=[{"_id": None, "result": 5}],
        msg="$first with descending sort should return largest value",
    ),
]

FIRST_SUCCESS_TESTS = FIRST_NULL_MISSING_TESTS + FIRST_EDGE_CASE_TESTS


@pytest.mark.parametrize("test_case", pytest_params(FIRST_SUCCESS_TESTS))
def test_accumulator_first_null_missing(collection, test_case: AccumulatorTestCase):
    """Test $first accumulator null, missing, and edge case behavior."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
