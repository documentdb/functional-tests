"""Tests for $sum accumulator: integer boundary values, large groups, and negative zero."""

from __future__ import annotations

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NEGATIVE_ZERO,
    DOUBLE_FROM_INT64_MAX,
    DOUBLE_NEGATIVE_ZERO,
    INT32_MAX,
    INT32_MAX_MINUS_1,
    INT32_MIN,
    INT32_MIN_PLUS_1,
    INT32_OVERFLOW,
    INT32_UNDERFLOW,
    INT64_MAX,
    INT64_MAX_MINUS_1,
    INT64_MIN,
    INT64_MIN_PLUS_1,
)

# Property [Integer Boundary Values]: boundary values at the edges of int32
# and Int64 ranges stay in their original type when no overflow occurs, and
# promote to the next wider type when the sum crosses the boundary by one.
SUM_INTEGER_BOUNDARY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "boundary_int32_max_single",
        docs=[{"v": INT32_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": INT32_MAX, "type": "int"},
        msg="$sum should keep int32_max as int32 when it is the only value",
    ),
    AccumulatorTestCase(
        "boundary_int32_min_single",
        docs=[{"v": INT32_MIN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": INT32_MIN, "type": "int"},
        msg="$sum should keep int32_min as int32 when it is the only value",
    ),
    AccumulatorTestCase(
        "boundary_int64_max_single",
        docs=[{"v": INT64_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": INT64_MAX, "type": "long"},
        msg="$sum should keep int64_max as Int64 when it is the only value",
    ),
    AccumulatorTestCase(
        "boundary_int64_min_single",
        docs=[{"v": INT64_MIN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": INT64_MIN, "type": "long"},
        msg="$sum should keep int64_min as Int64 when it is the only value",
    ),
    AccumulatorTestCase(
        "boundary_int32_max_no_overflow",
        docs=[{"v": INT32_MAX_MINUS_1}, {"v": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": INT32_MAX, "type": "int"},
        msg="$sum should stay int32 when int32_max-1 + 1 equals int32_max",
    ),
    AccumulatorTestCase(
        "boundary_int32_max_overflow",
        docs=[{"v": INT32_MAX_MINUS_1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": Int64(INT32_OVERFLOW), "type": "long"},
        msg="$sum should promote to Int64 when int32_max-1 + 2 overflows int32",
    ),
    AccumulatorTestCase(
        "boundary_int32_min_no_overflow",
        docs=[{"v": INT32_MIN_PLUS_1}, {"v": -1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": INT32_MIN, "type": "int"},
        msg="$sum should stay int32 when int32_min+1 + (-1) equals int32_min",
    ),
    AccumulatorTestCase(
        "boundary_int32_min_overflow",
        docs=[{"v": INT32_MIN_PLUS_1}, {"v": -2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": Int64(INT32_UNDERFLOW), "type": "long"},
        msg="$sum should promote to Int64 when int32_min+1 + (-2) overflows int32",
    ),
    AccumulatorTestCase(
        "boundary_int64_max_no_overflow",
        docs=[{"v": INT64_MAX_MINUS_1}, {"v": Int64(1)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": INT64_MAX, "type": "long"},
        msg="$sum should stay Int64 when int64_max-1 + 1 equals int64_max",
    ),
    AccumulatorTestCase(
        "boundary_int64_max_overflow",
        docs=[{"v": INT64_MAX_MINUS_1}, {"v": Int64(2)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": DOUBLE_FROM_INT64_MAX, "type": "double"},
        msg="$sum should promote to double when int64_max-1 + 2 overflows Int64",
    ),
    AccumulatorTestCase(
        "boundary_int64_min_no_overflow",
        docs=[{"v": INT64_MIN_PLUS_1}, {"v": Int64(-1)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": INT64_MIN, "type": "long"},
        msg="$sum should stay Int64 when int64_min+1 + (-1) equals int64_min",
    ),
    AccumulatorTestCase(
        "boundary_int64_min_overflow",
        docs=[{"v": INT64_MIN_PLUS_1}, {"v": Int64(-2)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": -DOUBLE_FROM_INT64_MAX, "type": "double"},
        msg="$sum should promote to double when int64_min+1 + (-2) overflows Int64",
    ),
]

# Property [Large Groups]: $sum correctly accumulates values across large
# groups without precision loss or type promotion.
SUM_LARGE_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "large_group_10k_int1",
        docs=[{"v": 1} for _ in range(10_000)],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": 10_000, "type": "int"},
        msg="$sum should produce 10000 (int32) for 10000 documents with int(1)",
    ),
]

SUM_BOUNDARY_AND_LARGE_GROUP_TESTS = SUM_INTEGER_BOUNDARY_TESTS + SUM_LARGE_GROUP_TESTS


@pytest.mark.parametrize("test_case", pytest_params(SUM_BOUNDARY_AND_LARGE_GROUP_TESTS))
def test_sum_boundary(collection, test_case: AccumulatorTestCase):
    """Test $sum integer boundary values and large group accumulation."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline or [], "cursor": {}},
    )
    assertSuccess(
        result,
        [test_case.expected],
        msg=test_case.msg,
    )


# Property [Negative Zero Normalization]: $sum normalizes negative zero to
# positive zero for both double and Decimal128.
SUM_NEGATIVE_ZERO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "neg_zero_double_single",
        docs=[{"v": DOUBLE_NEGATIVE_ZERO}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "str": {"$toString": "$result"}}},
        ],
        expected="0",
        msg="$sum should normalize a single double -0.0 to +0.0",
    ),
    AccumulatorTestCase(
        "neg_zero_double_sum",
        docs=[{"v": DOUBLE_NEGATIVE_ZERO}, {"v": DOUBLE_NEGATIVE_ZERO}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "str": {"$toString": "$result"}}},
        ],
        expected="0",
        msg="$sum should normalize -0.0 + -0.0 to +0.0",
    ),
    AccumulatorTestCase(
        "neg_zero_decimal128_single",
        docs=[{"v": DECIMAL128_NEGATIVE_ZERO}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "str": {"$toString": "$result"}}},
        ],
        expected="0",
        msg="$sum should normalize a single Decimal128('-0') to Decimal128('0')",
    ),
    AccumulatorTestCase(
        "neg_zero_decimal128_sum",
        docs=[{"v": DECIMAL128_NEGATIVE_ZERO}, {"v": DECIMAL128_NEGATIVE_ZERO}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "str": {"$toString": "$result"}}},
        ],
        expected="0",
        msg="$sum should normalize Decimal128('-0') + Decimal128('-0') to Decimal128('0')",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(SUM_NEGATIVE_ZERO_TESTS))
def test_sum_negative_zero(collection, test_case: AccumulatorTestCase):
    """Test $sum negative zero normalization."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline or [], "cursor": {}},
    )
    assertSuccess(
        result,
        [{"str": test_case.expected}],
        msg=test_case.msg,
    )
