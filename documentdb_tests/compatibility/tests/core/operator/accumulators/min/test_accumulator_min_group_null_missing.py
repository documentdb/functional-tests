"""Tests for $min accumulator — null/missing handling and edge cases ($group)."""

from __future__ import annotations

from typing import Any

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params


def _group_min(accumulator: Any) -> list[dict[str, Any]]:
    """Build a $group pipeline for $min."""
    return [{"$group": {"_id": None, "result": {"$min": accumulator}}}]


def _run_accumulator(collection, test_case: AccumulatorTestCase):
    """Insert docs and run the pipeline."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    return execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )


# ---------------------------------------------------------------------------
# Property [Null and Missing Ignored]: null values, missing fields, and $$REMOVE
# are excluded from the min computation. When no non-null/non-missing values
# remain, the result is null.
# ---------------------------------------------------------------------------
MIN_NULL_MISSING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "null_all",
        docs=[{"v": None}, {"v": None}, {"v": None}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": None}],
        msg="$min should return null when all values are null",
    ),
    AccumulatorTestCase(
        "missing_all",
        docs=[{"x": 1}, {"x": 2}, {"x": 3}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": None}],
        msg="$min should return null when all documents have missing field",
    ),
    AccumulatorTestCase(
        "null_and_missing_all",
        docs=[{"v": None}, {"x": 1}, {"v": None}, {"x": 2}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": None}],
        msg="$min should return null when all values are null or missing",
    ),
    AccumulatorTestCase(
        "null_single_among_values",
        docs=[{"v": 10}, {"v": None}, {"v": 20}, {"v": 5}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": 5}],
        msg="$min should exclude null and return min of remaining values",
    ),
    AccumulatorTestCase(
        "missing_single_among_values",
        docs=[{"v": 10}, {"x": 1}, {"v": 20}, {"v": 5}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": 5}],
        msg="$min should exclude missing and return min of remaining values",
    ),
    AccumulatorTestCase(
        "null_and_missing_among_values",
        docs=[{"v": 10}, {"v": None}, {"x": 1}, {"v": 5}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": 5}],
        msg="$min should exclude both null and missing from computation",
    ),
    AccumulatorTestCase(
        "null_one_value",
        docs=[{"v": None}, {"x": 1}, {"v": 42}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": 42}],
        msg="$min should return the only non-null/non-missing value",
    ),
    AccumulatorTestCase(
        "null_two_docs",
        docs=[{"v": None}, {"x": 1}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": None}],
        msg="$min should return null when only null and missing present",
    ),
    AccumulatorTestCase(
        "remove_via_cond",
        docs=[{"v": -1}, {"v": 5}, {"v": -2}, {"v": 10}],
        pipeline=_group_min({"$cond": [{"$gte": ["$v", 0]}, "$v", "$$REMOVE"]}),
        expected=[{"_id": None, "result": 5}],
        msg="$min should treat $$REMOVE as missing and exclude it",
    ),
    AccumulatorTestCase(
        "remove_all",
        docs=[{"v": -1}, {"v": -2}, {"v": -3}],
        pipeline=_group_min({"$cond": [{"$gte": ["$v", 0]}, "$v", "$$REMOVE"]}),
        expected=[{"_id": None, "result": None}],
        msg="$min should return null when all docs produce $$REMOVE",
    ),
    AccumulatorTestCase(
        "remove_with_values",
        docs=[{"v": -1}, {"v": 5}, {"v": -2}, {"v": 3}],
        pipeline=_group_min({"$cond": [{"$gte": ["$v", 0]}, "$v", "$$REMOVE"]}),
        expected=[{"_id": None, "result": 3}],
        msg="$min should return min of non-removed values",
    ),
]

# ---------------------------------------------------------------------------
# Property [Accumulator-Specific Edge Cases]: edge cases unique to accumulator context.
# ---------------------------------------------------------------------------
MIN_EDGE_CASE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "edge_single_doc",
        docs=[{"v": 42}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": 42}],
        msg="$min should return value when only one document in group",
    ),
    AccumulatorTestCase(
        "edge_single_null_doc",
        docs=[{"v": None}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": None}],
        msg="$min should return null for single null document",
    ),
    AccumulatorTestCase(
        "edge_single_missing_doc",
        docs=[{"x": 1}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": None}],
        msg="$min should return null for single document with missing field",
    ),
    AccumulatorTestCase(
        "edge_multi_group",
        docs=[
            {"g": "A", "v": 10},
            {"g": "A", "v": 5},
            {"g": "B", "v": 20},
            {"g": "B", "v": 15},
        ],
        pipeline=[
            {"$group": {"_id": "$g", "result": {"$min": "$v"}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[{"_id": "A", "result": 5}, {"_id": "B", "result": 15}],
        msg="$min should compute independently per group",
    ),
    AccumulatorTestCase(
        "edge_many_docs",
        docs=[{"v": i} for i in range(100, 0, -1)],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": 1}],
        msg="$min should correctly compute over 100+ documents",
    ),
    AccumulatorTestCase(
        "edge_array_field_not_traversed",
        docs=[{"v": [5, 1, 8]}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": [5, 1, 8]}],
        msg="$min should treat array field as a whole value, not traverse elements",
    ),
    AccumulatorTestCase(
        "edge_mixed_array_scalar",
        docs=[{"v": [1, 2, 3]}, {"v": 5}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": 5}],
        msg="$min should pick scalar Number over Array (Number < Array in BSON)",
    ),
]

# ---------------------------------------------------------------------------
# Combined success tests
# ---------------------------------------------------------------------------
MIN_GROUP_NULL_MISSING_SUCCESS_TESTS = MIN_NULL_MISSING_TESTS + MIN_EDGE_CASE_TESTS


@pytest.mark.parametrize("test_case", pytest_params(MIN_GROUP_NULL_MISSING_SUCCESS_TESTS))
def test_accumulator_min_group_null_missing(collection, test_case: AccumulatorTestCase):
    """Test $min accumulator null/missing handling and edge cases with $group."""
    result = _run_accumulator(collection, test_case)
    assertSuccess(result, test_case.expected, msg=test_case.msg)
