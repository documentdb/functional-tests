"""Tests for $addToSet accumulator null and missing field handling."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# ---------------------------------------------------------------------------
# Property lists
# ---------------------------------------------------------------------------

# Property [Null Collected]: null values are collected as valid values and deduplicated.
ADDTOSET_NULL_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "null_all",
        docs=[{"v": None}, {"v": None}, {"v": None}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [None]}],
        msg="$addToSet should collect null and deduplicate to a single null",
    ),
    AccumulatorTestCase(
        "null_single",
        docs=[{"v": None}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [None]}],
        msg="$addToSet should collect a single null value",
    ),
    AccumulatorTestCase(
        "null_among_values",
        docs=[{"v": None}, {"v": 5}, {"v": 3}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [None, 5, 3]}],
        msg="$addToSet should collect null alongside other values",
    ),
    AccumulatorTestCase(
        "null_and_values_dedup",
        docs=[{"v": 10}, {"v": None}, {"v": 5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [10, None, 5]}],
        msg="$addToSet should collect null and distinct values without duplication",
    ),
]

# Property [Missing Excluded]: missing fields are excluded from the result.
ADDTOSET_MISSING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "missing_all",
        docs=[{"x": 1}, {"x": 2}, {"x": 3}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": []}],
        msg="$addToSet should return empty array when all fields are missing",
    ),
    AccumulatorTestCase(
        "missing_single",
        docs=[{"x": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": []}],
        msg="$addToSet should return empty array for a single doc with missing field",
    ),
    AccumulatorTestCase(
        "missing_among_values",
        docs=[{"x": 1}, {"v": 5}, {"v": 3}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [5, 3]}],
        msg="$addToSet should exclude missing fields and collect only present values",
    ),
]

# Property [Null and Missing Combined]: null is collected while missing is excluded.
ADDTOSET_NULL_MISSING_COMBINED_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "combined_null_and_missing",
        docs=[{"v": None}, {"x": 1}, {"v": None}, {"x": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [None]}],
        msg="$addToSet should collect null but exclude missing fields",
    ),
    AccumulatorTestCase(
        "combined_null_missing_and_values",
        docs=[{"v": 10}, {"v": None}, {"x": 1}, {"v": 5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [10, None, 5]}],
        msg="$addToSet should collect null and values but exclude missing fields",
    ),
]

# ---------------------------------------------------------------------------
# Aggregate
# ---------------------------------------------------------------------------

ADDTOSET_NULL_MISSING_TESTS = (
    ADDTOSET_NULL_TESTS + ADDTOSET_MISSING_TESTS + ADDTOSET_NULL_MISSING_COMBINED_TESTS
)

# ---------------------------------------------------------------------------
# Test function
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("test_case", pytest_params(ADDTOSET_NULL_MISSING_TESTS))
def test_accumulator_addToSet_null_missing(collection, test_case: AccumulatorTestCase):
    """Test $addToSet accumulator null and missing field handling."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg, ignore_order_in=["result"])
