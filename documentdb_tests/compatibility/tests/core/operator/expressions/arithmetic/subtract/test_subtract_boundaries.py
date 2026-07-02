"""Boundary and overflow tests for the $subtract operator."""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_JUST_ABOVE_HALF,
    DECIMAL128_JUST_BELOW_HALF,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MANY_TRAILING_ZEROS,
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_SMALL_EXPONENT,
    DECIMAL128_TRAILING_ZERO,
    DOUBLE_JUST_ABOVE_HALF,
    DOUBLE_JUST_BELOW_HALF,
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    DOUBLE_NEAR_MIN,
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

# Property [Int32 Boundaries]: $subtract at int32 limits promotes results when needed.
SUBTRACT_INT32_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_overflow",
        doc={},
        expression={"$subtract": [INT32_MAX, -1]},
        expected=Int64(INT32_OVERFLOW),
        msg="Should promote int32 overflow result to int64",
    ),
    ExpressionTestCase(
        "int32_underflow",
        doc={},
        expression={"$subtract": [INT32_MIN, 1]},
        expected=Int64(INT32_UNDERFLOW),
        msg="Should promote int32 underflow result to int64",
    ),
    ExpressionTestCase(
        "int32_max_minuend",
        doc={},
        expression={"$subtract": [INT32_MAX, 10]},
        expected=2147483637,
        msg="Should subtract from INT32_MAX",
    ),
    ExpressionTestCase(
        "int32_max_minus_1_minuend",
        doc={},
        expression={"$subtract": [INT32_MAX_MINUS_1, 10]},
        expected=2147483636,
        msg="Should subtract from INT32_MAX-1",
    ),
    ExpressionTestCase(
        "int32_min_minuend",
        doc={},
        expression={"$subtract": [INT32_MIN, 10]},
        expected=Int64(-2147483658),
        msg="Should subtract from INT32_MIN",
    ),
    ExpressionTestCase(
        "int32_min_plus_1_minuend",
        doc={},
        expression={"$subtract": [INT32_MIN_PLUS_1, 10]},
        expected=Int64(-2147483657),
        msg="Should subtract from INT32_MIN+1",
    ),
    ExpressionTestCase(
        "int32_max_subtrahend",
        doc={},
        expression={"$subtract": [10, INT32_MAX]},
        expected=-2147483637,
        msg="Should subtract INT32_MAX",
    ),
    ExpressionTestCase(
        "int32_min_subtrahend",
        doc={},
        expression={"$subtract": [10, INT32_MIN]},
        expected=Int64(2147483658),
        msg="Should subtract INT32_MIN",
    ),
]

# Property [Int64 Boundaries]: $subtract at int64 limits overflows to double.
SUBTRACT_INT64_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int64_overflow",
        doc={},
        expression={"$subtract": [INT64_MAX, -1]},
        expected=9.223372036854776e18,
        msg="Should overflow int64 subtraction to double",
    ),
    ExpressionTestCase(
        "int64_underflow",
        doc={},
        expression={"$subtract": [INT64_MIN, 1]},
        expected=-9.223372036854776e18,
        msg="Should underflow int64 subtraction to double",
    ),
    ExpressionTestCase(
        "int64_max_minuend",
        doc={},
        expression={"$subtract": [INT64_MAX, Int64(10)]},
        expected=Int64(9223372036854775797),
        msg="Should subtract from INT64_MAX",
    ),
    ExpressionTestCase(
        "int64_max_minus_1_minuend",
        doc={},
        expression={"$subtract": [INT64_MAX_MINUS_1, Int64(10)]},
        expected=Int64(9223372036854775796),
        msg="Should subtract from INT64_MAX-1",
    ),
    ExpressionTestCase(
        "int64_min_minuend",
        doc={},
        expression={"$subtract": [INT64_MIN, Int64(10)]},
        expected=-9.223372036854776e18,
        msg="Should subtract from INT64_MIN",
    ),
    ExpressionTestCase(
        "int64_min_plus_1_minuend",
        doc={},
        expression={"$subtract": [INT64_MIN_PLUS_1, Int64(10)]},
        expected=-9.223372036854776e18,
        msg="Should subtract from INT64_MIN+1",
    ),
    ExpressionTestCase(
        "int64_max_subtrahend",
        doc={},
        expression={"$subtract": [Int64(10), INT64_MAX]},
        expected=Int64(-9223372036854775797),
        msg="Should subtract INT64_MAX",
    ),
    ExpressionTestCase(
        "int64_min_subtrahend",
        doc={},
        expression={"$subtract": [Int64(10), INT64_MIN]},
        expected=9.223372036854776e18,
        msg="Should subtract INT64_MIN",
    ),
]

# Property [Double Boundaries]: $subtract handles double extremes.
SUBTRACT_DOUBLE_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "double_overflow",
        doc={},
        expression={"$subtract": [1e308, -1e308]},
        expected=float("inf"),
        msg="Should overflow double subtraction to infinity",
    ),
    ExpressionTestCase(
        "double_underflow",
        doc={},
        expression={"$subtract": [-1e308, 1e308]},
        expected=float("-inf"),
        msg="Should underflow double subtraction to negative infinity",
    ),
    ExpressionTestCase(
        "double_min_subnormal_minuend",
        doc={},
        expression={"$subtract": [DOUBLE_MIN_SUBNORMAL, 0]},
        expected=5e-324,
        msg="Should subtract from smallest subnormal double",
    ),
    ExpressionTestCase(
        "double_near_min_minuend",
        doc={},
        expression={"$subtract": [DOUBLE_NEAR_MIN, 0]},
        expected=1e-308,
        msg="Should subtract from near-min double",
    ),
    ExpressionTestCase(
        "double_near_max_minuend",
        doc={},
        expression={"$subtract": [DOUBLE_NEAR_MAX, 1e307]},
        expected=9e307,
        msg="Should subtract near-max double",
    ),
    ExpressionTestCase(
        "double_max_safe_integer_minuend",
        doc={},
        expression={"$subtract": [float(DOUBLE_MAX_SAFE_INTEGER), 1]},
        expected=9007199254740991.0,
        msg="Should subtract from max safe integer double",
    ),
    ExpressionTestCase(
        "double_max_safe_integer_subtrahend",
        doc={},
        expression={"$subtract": [1, float(DOUBLE_MAX_SAFE_INTEGER)]},
        expected=-9007199254740991.0,
        msg="Should subtract max safe integer double",
    ),
    ExpressionTestCase(
        "double_half_minuend",
        doc={},
        expression={"$subtract": [0.5, 0.25]},
        expected=0.25,
        msg="Should subtract double half boundary",
    ),
    ExpressionTestCase(
        "double_one_and_half_minuend",
        doc={},
        expression={"$subtract": [1.5, 0.5]},
        expected=1.0,
        msg="Should subtract double one-and-half boundary",
    ),
    ExpressionTestCase(
        "double_two_and_half_minuend",
        doc={},
        expression={"$subtract": [2.5, 1.5]},
        expected=1.0,
        msg="Should subtract double two-and-half boundary",
    ),
    ExpressionTestCase(
        "double_negative_half_minuend",
        doc={},
        expression={"$subtract": [-0.5, 0.5]},
        expected=-1.0,
        msg="Should subtract double negative half boundary",
    ),
    ExpressionTestCase(
        "double_negative_one_and_half_minuend",
        doc={},
        expression={"$subtract": [-1.5, 0.5]},
        expected=-2.0,
        msg="Should subtract double negative one-and-half boundary",
    ),
    ExpressionTestCase(
        "double_just_below_half_minuend",
        doc={},
        expression={"$subtract": [DOUBLE_JUST_BELOW_HALF, 0.25]},
        expected=pytest.approx(0.2499999999999994),
        msg="Should subtract double just below half boundary",
    ),
    ExpressionTestCase(
        "double_just_above_half_minuend",
        doc={},
        expression={"$subtract": [DOUBLE_JUST_ABOVE_HALF, 0.25]},
        expected=pytest.approx(0.250000001),
        msg="Should subtract double just above half boundary",
    ),
]

# Property [Decimal128 Boundaries]: $subtract preserves decimal128 precision and extremes.
SUBTRACT_DECIMAL_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "decimal128_max_minuend",
        doc={},
        expression={"$subtract": [DECIMAL128_MAX, Decimal128("1")]},
        expected=DECIMAL128_MAX,
        msg="Should subtract from decimal128 max",
    ),
    ExpressionTestCase(
        "decimal128_min_minuend",
        doc={},
        expression={"$subtract": [DECIMAL128_MIN, Decimal128("1")]},
        expected=DECIMAL128_MIN,
        msg="Should subtract from decimal128 min",
    ),
    ExpressionTestCase(
        "decimal128_small_exponent_minuend",
        doc={},
        expression={"$subtract": [DECIMAL128_SMALL_EXPONENT, Decimal128("0")]},
        expected=DECIMAL128_SMALL_EXPONENT,
        msg="Should subtract from decimal128 with small exponent",
    ),
    ExpressionTestCase(
        "decimal128_large_exponent_minuend",
        doc={},
        expression={"$subtract": [DECIMAL128_LARGE_EXPONENT, Decimal128("1")]},
        expected=DECIMAL128_LARGE_EXPONENT,
        msg="Should subtract from decimal128 with large exponent",
    ),
    ExpressionTestCase(
        "decimal128_trailing_zero",
        doc={},
        expression={"$subtract": [DECIMAL128_TRAILING_ZERO, Decimal128("0.5")]},
        expected=Decimal128("0.5"),
        msg="Should preserve decimal128 trailing zero",
    ),
    ExpressionTestCase(
        "decimal128_many_trailing_zeros",
        doc={},
        expression={"$subtract": [DECIMAL128_MANY_TRAILING_ZEROS, Decimal128("0.5")]},
        expected=Decimal128("0.50000000000000000000000000000000"),
        msg="Should preserve decimal128 many trailing zeros",
    ),
    ExpressionTestCase(
        "decimal_half_minuend",
        doc={},
        expression={"$subtract": [Decimal128("0.5"), Decimal128("0.25")]},
        expected=Decimal128("0.25"),
        msg="Should subtract decimal half boundary",
    ),
    ExpressionTestCase(
        "decimal_one_and_half_minuend",
        doc={},
        expression={"$subtract": [Decimal128("1.5"), Decimal128("0.5")]},
        expected=Decimal128("1.0"),
        msg="Should subtract decimal one-and-half boundary",
    ),
    ExpressionTestCase(
        "decimal_two_and_half_minuend",
        doc={},
        expression={"$subtract": [Decimal128("2.5"), Decimal128("1.5")]},
        expected=Decimal128("1.0"),
        msg="Should subtract decimal two-and-half boundary",
    ),
    ExpressionTestCase(
        "decimal_negative_half_minuend",
        doc={},
        expression={"$subtract": [Decimal128("-0.5"), Decimal128("0.5")]},
        expected=Decimal128("-1.0"),
        msg="Should subtract decimal negative half boundary",
    ),
    ExpressionTestCase(
        "decimal_negative_one_and_half_minuend",
        doc={},
        expression={"$subtract": [Decimal128("-1.5"), Decimal128("0.5")]},
        expected=Decimal128("-2.0"),
        msg="Should subtract decimal negative one-and-half boundary",
    ),
    ExpressionTestCase(
        "decimal_just_below_half_minuend",
        doc={},
        expression={"$subtract": [DECIMAL128_JUST_BELOW_HALF, Decimal128("0.25")]},
        expected=Decimal128("0.2499999999999999999999999999999999"),
        msg="Should subtract decimal just below half boundary",
    ),
    ExpressionTestCase(
        "decimal_just_above_half_minuend",
        doc={},
        expression={"$subtract": [DECIMAL128_JUST_ABOVE_HALF, Decimal128("0.25")]},
        expected=Decimal128("0.2500000000000000000000000000000001"),
        msg="Should subtract decimal just above half boundary",
    ),
]

SUBTRACT_BOUNDARY_TESTS = (
    SUBTRACT_INT32_BOUNDARY_TESTS
    + SUBTRACT_INT64_BOUNDARY_TESTS
    + SUBTRACT_DOUBLE_BOUNDARY_TESTS
    + SUBTRACT_DECIMAL_BOUNDARY_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SUBTRACT_BOUNDARY_TESTS))
def test_subtract_boundaries(collection, test_case: ExpressionTestCase):
    """Test $subtract boundary and overflow cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
