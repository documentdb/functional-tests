"""
Tests for $avg accumulator null and missing value handling in $group context.

Covers null values, missing fields, $$REMOVE, and combinations with numeric values.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Null and Missing Ignored]: null values, missing fields, and
# $$REMOVE are treated as non-numeric and excluded from both the sum and
# count, producing null when no numeric values remain.
AVG_NULL_MISSING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "all_null",
        docs=[{"_id": 0, "v": None}, {"_id": 1, "v": None}, {"_id": 2, "v": None}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": None}],
        msg="$avg should return null when all values in the group are null",
    ),
    AccumulatorTestCase(
        "single_null",
        docs=[{"v": None}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should return null when the only value is null",
    ),
    AccumulatorTestCase(
        "some_null",
        docs=[{"_id": 0, "v": 10}, {"_id": 1, "v": None}, {"_id": 2, "v": 30}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": 20.0}],
        msg="$avg should exclude null from both sum and count",
    ),
    AccumulatorTestCase(
        "all_missing",
        docs=[{"_id": 0, "other": 0}, {"_id": 1, "other": 1}, {"_id": 2, "other": 2}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": None}],
        msg="$avg should return null when all values reference missing fields",
    ),
    AccumulatorTestCase(
        "single_missing",
        docs=[{"x": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should return null when the only value is a missing field",
    ),
    AccumulatorTestCase(
        "some_missing",
        docs=[{"_id": 0, "v": 10}, {"_id": 1}, {"_id": 2, "v": 30}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": 20.0}],
        msg="$avg should exclude missing fields from both sum and count",
    ),
    AccumulatorTestCase(
        "mixed_null_and_missing_no_numerics",
        docs=[{"v": None}, {"x": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should return null when values are a mix of null and missing",
    ),
    AccumulatorTestCase(
        "mix_null_missing_numeric",
        docs=[
            {"_id": 0, "v": 10},
            {"_id": 1, "v": None},
            {"_id": 2},
            {"_id": 3, "v": 30},
        ],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": 20.0}],
        msg="Only numeric values should contribute to average",
    ),
    AccumulatorTestCase(
        "remove_only",
        docs=[{"v": 5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": {"$cond": [False, 1, "$$REMOVE"]}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should treat $$REMOVE as missing and return null",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(AVG_NULL_MISSING_TESTS))
def test_accumulator_avg_null_missing(collection, test_case: AccumulatorTestCase):
    """Test $avg null and missing value handling in $group context."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(result, expected=test_case.expected, msg=test_case.msg)
