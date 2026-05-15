"""
Tests for $avg accumulator boundary values and overflow in $group context.

Covers int32/int64 boundary values, double boundary values (subnormal, normal,
near-max), Decimal128 precision and boundary values, and sum overflow behavior.
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
    DECIMAL128_INFINITY,
    DECIMAL128_INT64_OVERFLOW,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_SMALL_EXPONENT,
    DECIMAL128_TRAILING_ZERO,
    DOUBLE_FROM_INT64_MAX,
    DOUBLE_MAX,
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    DOUBLE_MIN_NORMAL,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    DOUBLE_NEAR_MIN,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    INT32_MAX,
    INT32_MAX_MINUS_1,
    INT32_MIN,
    INT64_MAX,
    INT64_MAX_MINUS_1,
    INT64_MIN,
    INT64_MIN_PLUS_1,
    INT64_ZERO,
)

# Property [Integer Boundaries]: $avg handles int32 and int64 boundary values
# including MAX, MIN, adjacent values, and overflow combinations.
AVG_INT_BOUNDARY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        id="int32_zeros",
        docs=[{"v": 0}, {"v": 0}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DOUBLE_ZERO}],
        msg="$avg should return 0.0 for two int32 zeros",
    ),
    AccumulatorTestCase(
        id="int32_one_neg_one",
        docs=[{"v": 1}, {"v": -1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DOUBLE_ZERO}],
        msg="$avg should return 0.0 for int32 1 and -1",
    ),
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
        id="int32_adjacent_max",
        docs=[{"v": INT32_MAX_MINUS_1}, {"v": INT32_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 2_147_483_646.5}],
        msg="$avg of adjacent int32 MAX values should produce exact double",
    ),
    AccumulatorTestCase(
        id="int32_adjacent_min",
        docs=[{"v": INT32_MIN}, {"v": INT32_MIN + 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": -2_147_483_647.5}],
        msg="$avg of adjacent int32 MIN values should produce exact double",
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
        id="int64_max_and_zero",
        docs=[{"v": INT64_MAX}, {"v": INT64_ZERO}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DOUBLE_FROM_INT64_MAX / 2}],
        msg="$avg should handle int64 MAX with precision loss in double",
    ),
    AccumulatorTestCase(
        id="int64_max_and_min",
        docs=[{"v": INT64_MAX}, {"v": INT64_MIN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": -0.5}],
        msg="$avg should handle int64 MAX and MIN together",
    ),
    AccumulatorTestCase(
        id="int64_max_and_one",
        docs=[{"_id": 0, "v": INT64_MAX}, {"_id": 1, "v": Int64(1)}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": 4.611686018427388e18}],
        msg="avg of INT64_MAX and 1",
    ),
    AccumulatorTestCase(
        id="int64_adjacent_max",
        docs=[{"v": INT64_MAX_MINUS_1}, {"v": INT64_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DOUBLE_FROM_INT64_MAX}],
        msg="$avg of adjacent int64 MAX values should produce double with precision loss",
    ),
    AccumulatorTestCase(
        id="int64_adjacent_min",
        docs=[{"v": INT64_MIN_PLUS_1}, {"v": INT64_MIN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": -DOUBLE_FROM_INT64_MAX}],
        msg="$avg of adjacent int64 MIN values should produce double with precision loss",
    ),
]

# Property [Double Boundaries]: $avg handles double boundary values
# including subnormal, minimum normal, near-max, and max safe integer.
AVG_DOUBLE_BOUNDARY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        id="double_whole_number",
        docs=[{"v": 3.0}, {"v": 5.0}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 4.0}],
        msg="$avg should produce correct average for whole-number floats",
    ),
    AccumulatorTestCase(
        id="double_subnormal_positive",
        docs=[{"v": DOUBLE_MIN_SUBNORMAL}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DOUBLE_MIN_SUBNORMAL}],
        msg="$avg should handle positive subnormal value correctly",
    ),
    AccumulatorTestCase(
        id="double_subnormal_negative",
        docs=[{"v": DOUBLE_MIN_NEGATIVE_SUBNORMAL}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DOUBLE_MIN_NEGATIVE_SUBNORMAL}],
        msg="$avg should handle negative subnormal value correctly",
    ),
    AccumulatorTestCase(
        id="double_subnormal_pair",
        docs=[
            {"_id": 0, "v": DOUBLE_MIN_SUBNORMAL},
            {"_id": 1, "v": DOUBLE_MIN_SUBNORMAL},
        ],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": DOUBLE_MIN_SUBNORMAL}],
        msg="avg of two subnormal doubles should return subnormal",
    ),
    AccumulatorTestCase(
        id="double_min_normal",
        docs=[{"v": DOUBLE_MIN_NORMAL}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DOUBLE_MIN_NORMAL}],
        msg="$avg should handle smallest positive normal double correctly",
    ),
    AccumulatorTestCase(
        id="double_max_single",
        docs=[{"v": DOUBLE_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DOUBLE_MAX}],
        msg="$avg should handle DBL_MAX as a single value correctly",
    ),
    AccumulatorTestCase(
        id="double_max_safe_integer",
        docs=[{"v": float(DOUBLE_MAX_SAFE_INTEGER)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": float(DOUBLE_MAX_SAFE_INTEGER)}],
        msg="$avg should handle max safe integer value correctly",
    ),
    AccumulatorTestCase(
        id="double_max_safe_integer_pair",
        docs=[
            {"v": float(DOUBLE_MAX_SAFE_INTEGER)},
            {"v": float(DOUBLE_MAX_SAFE_INTEGER)},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": float(DOUBLE_MAX_SAFE_INTEGER)}],
        msg="$avg of two max safe integer values should return that value",
    ),
    AccumulatorTestCase(
        id="double_near_min_pair",
        docs=[{"v": DOUBLE_NEAR_MIN}, {"v": DOUBLE_NEAR_MIN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DOUBLE_NEAR_MIN}],
        msg="$avg should handle values near minimum normal correctly",
    ),
    AccumulatorTestCase(
        id="double_near_max_single",
        docs=[{"v": DOUBLE_NEAR_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DOUBLE_NEAR_MAX}],
        msg="$avg should handle values near maximum finite correctly",
    ),
    AccumulatorTestCase(
        id="double_near_max_pair",
        docs=[{"_id": 0, "v": DOUBLE_NEAR_MAX}, {"_id": 1, "v": DOUBLE_NEAR_MAX}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": float("inf")}],
        msg="avg of two DOUBLE_NEAR_MAX overflows sum to inf",
    ),
]

# Property [Decimal128 Precision]: $avg preserves Decimal128 precision
# across extreme exponent differences, trailing zeros, and boundary values.
AVG_DECIMAL128_BOUNDARY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        id="decimal128_full_precision",
        docs=[
            {"v": Decimal128("1.000000000000000000000000000000001")},
            {"v": Decimal128("1.000000000000000000000000000000003")},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Decimal128("1.000000000000000000000000000000002")}],
        msg="$avg should preserve full 34-digit Decimal128 precision",
    ),
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
        id="decimal128_34_digit_integer",
        docs=[
            {"v": Decimal128("1234567890123456789012345678901234")},
            {"v": Decimal128("1234567890123456789012345678901234")},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Decimal128("1234567890123456789012345678901234")}],
        msg="$avg should preserve 34-digit integer Decimal128 values",
    ),
    AccumulatorTestCase(
        id="decimal128_trailing_zeros",
        docs=[{"v": Decimal128("2.00")}, {"v": Decimal128("4.00")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Decimal128("3.00")}],
        msg="$avg should preserve trailing zeros in Decimal128 results",
    ),
    AccumulatorTestCase(
        id="decimal128_trailing_zeros_single_digit",
        docs=[{"v": DECIMAL128_TRAILING_ZERO}, {"v": Decimal128("3.0")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Decimal128("2.0")}],
        msg="$avg should preserve single trailing zero in Decimal128 results",
    ),
    AccumulatorTestCase(
        id="decimal128_subnormal_pair",
        docs=[{"v": DECIMAL128_MIN_POSITIVE}, {"v": DECIMAL128_MIN_POSITIVE}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DECIMAL128_MIN_POSITIVE}],
        msg="$avg should handle Decimal128 subnormal values correctly",
    ),
    AccumulatorTestCase(
        id="decimal128_subnormal_single",
        docs=[{"v": DECIMAL128_MIN_POSITIVE}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DECIMAL128_MIN_POSITIVE}],
        msg="$avg should handle a single Decimal128 subnormal value",
    ),
    AccumulatorTestCase(
        id="decimal128_near_max_single",
        docs=[{"v": DECIMAL128_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DECIMAL128_MAX}],
        msg="$avg should handle a single near-maximum Decimal128 value",
    ),
    AccumulatorTestCase(
        id="decimal128_near_max_with_small",
        docs=[{"v": DECIMAL128_MAX}, {"v": Decimal128("1")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Decimal128("5.000000000000000000000000000000000E+6144")}],
        msg="$avg should handle near-maximum Decimal128 averaged with a small value",
    ),
    AccumulatorTestCase(
        id="decimal128_max_and_min",
        docs=[{"_id": 0, "v": DECIMAL128_MAX}, {"_id": 1, "v": DECIMAL128_MIN}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": Decimal128("0")}],
        msg="avg of DECIMAL128_MAX and DECIMAL128_MIN",
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
    AccumulatorTestCase(
        id="decimal128_exceeds_int64",
        docs=[
            {"v": DECIMAL128_INT64_OVERFLOW},
            {"v": DECIMAL128_INT64_OVERFLOW},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DECIMAL128_INT64_OVERFLOW}],
        msg="$avg should produce Decimal128 for values exceeding int64 range",
    ),
]

# Property [Overflow]: sum overflow during accumulation produces Infinity for
# doubles and Decimal128, and int32/int64 overflow is handled via type
# promotion without error.
AVG_OVERFLOW_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        id="overflow_double_max",
        docs=[{"v": DOUBLE_MAX}, {"v": DOUBLE_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": FLOAT_INFINITY}],
        msg="$avg should return Infinity when two DBL_MAX values overflow the sum",
    ),
    AccumulatorTestCase(
        id="overflow_decimal128_max",
        docs=[{"v": DECIMAL128_MAX}, {"v": DECIMAL128_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DECIMAL128_INFINITY}],
        msg="$avg should return Decimal128 Infinity when two Decimal128 max values overflow",
    ),
    AccumulatorTestCase(
        id="overflow_int32_sum",
        docs=[{"v": INT32_MAX}, {"v": INT32_MAX}, {"v": INT32_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": float(INT32_MAX)}],
        msg="$avg should handle int32 sum overflow via type promotion without error",
    ),
    AccumulatorTestCase(
        id="overflow_int64_sum",
        docs=[{"v": INT64_MAX}, {"v": INT64_MAX}, {"v": INT64_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DOUBLE_FROM_INT64_MAX}],
        msg="$avg should handle int64 sum overflow by converting to double",
    ),
]

AVG_GROUP_BOUNDARY_TESTS: list[AccumulatorTestCase] = (
    AVG_INT_BOUNDARY_TESTS
    + AVG_DOUBLE_BOUNDARY_TESTS
    + AVG_DECIMAL128_BOUNDARY_TESTS
    + AVG_OVERFLOW_TESTS
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
