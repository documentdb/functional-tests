"""
Tests for $avg accumulator overflow, boundary values, and decimal128 precision
in $group context.

These test the accumulator's running sum behavior across documents,
which differs from expression-context evaluation on a single array.
"""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_SMALL_EXPONENT,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
)

# Property [Integer Boundaries]: $avg handles int32 and int64 boundary values
# including MAX, MIN, and overflow combinations.

AVG_INT_BOUNDARY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        id="int32_max_pair",
        docs=[{"_id": 0, "v": INT32_MAX}, {"_id": 1, "v": INT32_MAX}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": float(INT32_MAX)}],
        msg="avg of two INT32_MAX should return INT32_MAX as double",
    ),
    AccumulatorTestCase(
        id="int32_min_pair",
        docs=[{"_id": 0, "v": INT32_MIN}, {"_id": 1, "v": INT32_MIN}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": float(INT32_MIN)}],
        msg="avg of two INT32_MIN should return INT32_MIN as double",
    ),
    AccumulatorTestCase(
        id="int32_max_and_min",
        docs=[{"_id": 0, "v": INT32_MAX}, {"_id": 1, "v": INT32_MIN}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        # (2147483647 + -2147483648) / 2 = -0.5
        expected=[{"_id": None, "avg": -0.5}],
        msg="avg of INT32_MAX and INT32_MIN should be -0.5",
    ),
    AccumulatorTestCase(
        id="int64_max_pair",
        docs=[{"_id": 0, "v": INT64_MAX}, {"_id": 1, "v": INT64_MAX}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": 9.223372036854776e18}],
        msg="avg of two INT64_MAX should handle overflow",
    ),
    AccumulatorTestCase(
        id="int64_min_pair",
        docs=[{"_id": 0, "v": INT64_MIN}, {"_id": 1, "v": INT64_MIN}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": -9.223372036854776e18}],
        msg="avg of two INT64_MIN should handle overflow",
    ),
    AccumulatorTestCase(
        id="int64_max_and_one",
        docs=[{"_id": 0, "v": INT64_MAX}, {"_id": 1, "v": Int64(1)}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": 4.611686018427388e18}],
        msg="avg of INT64_MAX and 1",
    ),
]

# Property [Double Boundaries]: $avg handles double boundary values
# including near-max overflow and subnormal values.

AVG_DOUBLE_BOUNDARY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        id="double_near_max_pair",
        docs=[{"_id": 0, "v": DOUBLE_NEAR_MAX}, {"_id": 1, "v": DOUBLE_NEAR_MAX}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": float("inf")}],
        msg="avg of two DOUBLE_NEAR_MAX overflows sum to inf",
    ),
    AccumulatorTestCase(
        id="double_subnormal",
        docs=[
            {"_id": 0, "v": DOUBLE_MIN_SUBNORMAL},
            {"_id": 1, "v": DOUBLE_MIN_SUBNORMAL},
        ],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": DOUBLE_MIN_SUBNORMAL}],
        msg="avg of two subnormal doubles should return subnormal",
    ),
]

# Property [Decimal128 Precision]: $avg preserves Decimal128 precision
# across extreme exponent differences and boundary values.

AVG_DECIMAL128_PRECISION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        id="decimal128_high_precision",
        docs=[
            {
                "_id": 0,
                "v": Decimal128("1.000000000000000000000000000000001"),
            },
            {
                "_id": 1,
                "v": Decimal128("2.999999999999999999999999999999999"),
            },
        ],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": Decimal128("2.000000000000000000000000000000000")}],
        msg="decimal128 avg should preserve high precision",
    ),
    AccumulatorTestCase(
        id="decimal128_large_exponent",
        docs=[
            {"_id": 0, "v": DECIMAL128_LARGE_EXPONENT},
            {"_id": 1, "v": DECIMAL128_LARGE_EXPONENT},
        ],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": DECIMAL128_LARGE_EXPONENT}],
        msg="avg of two identical large exponent values should return same value",
    ),
    AccumulatorTestCase(
        id="decimal128_small_exponent",
        docs=[
            {"_id": 0, "v": DECIMAL128_SMALL_EXPONENT},
            {"_id": 1, "v": DECIMAL128_SMALL_EXPONENT},
        ],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": DECIMAL128_SMALL_EXPONENT}],
        msg="avg of two identical small exponent values should return same value",
    ),
    AccumulatorTestCase(
        id="decimal128_max_and_min",
        docs=[{"_id": 0, "v": DECIMAL128_MAX}, {"_id": 1, "v": DECIMAL128_MIN}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": Decimal128("0")}],
        msg="avg of DECIMAL128_MAX and DECIMAL128_MIN",
    ),
    AccumulatorTestCase(
        id="decimal128_extreme_exponent_diff",
        docs=[
            {"_id": 0, "v": Decimal128("1E+6144")},
            {"_id": 1, "v": Decimal128("1")},
        ],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[
            {
                "_id": None,
                "avg": Decimal128("5.00000000000000000000000000000000E+6143"),
            }
        ],
        msg="avg with extreme exponent difference",
    ),
]

AVG_GROUP_BOUNDARY_TESTS: list[AccumulatorTestCase] = (
    AVG_INT_BOUNDARY_TESTS + AVG_DOUBLE_BOUNDARY_TESTS + AVG_DECIMAL128_PRECISION_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(AVG_GROUP_BOUNDARY_TESTS))
def test_avg_group_boundaries(collection, test_case: AccumulatorTestCase):
    """Test $avg accumulator boundary values in $group context."""
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
