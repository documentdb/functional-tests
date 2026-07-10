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
    DECIMAL128_HALF,
    DECIMAL128_JUST_ABOVE_HALF,
    DECIMAL128_JUST_BELOW_HALF,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MANY_TRAILING_ZEROS,
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_NEGATIVE_HALF,
    DECIMAL128_NEGATIVE_ONE_AND_HALF,
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_SMALL_EXPONENT,
    DECIMAL128_TRAILING_ZERO,
    DECIMAL128_TWO_AND_HALF,
    DOUBLE_HALF,
    DOUBLE_JUST_ABOVE_HALF,
    DOUBLE_JUST_BELOW_HALF,
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    DOUBLE_NEAR_MIN,
    DOUBLE_NEGATIVE_HALF,
    DOUBLE_NEGATIVE_ONE_AND_HALF,
    DOUBLE_ONE_AND_HALF,
    DOUBLE_TWO_AND_HALF,
    FLOAT_INFINITY,
    FLOAT_NEGATIVE_INFINITY,
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

pytestmark = pytest.mark.aggregate

# Property [Int32 overflow]: $subtract promotes int32 results to int64 on overflow/underflow.
# Property [Int64 overflow]: $subtract promotes int64 results to double on overflow/underflow.
# Property [Double overflow]: $subtract returns ±Infinity on double overflow.
# Property [Decimal128 precision]: $subtract preserves Decimal128 full precision.
SUBTRACT_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    # Int32 overflow and underflow
    ExpressionTestCase(
        "int32_overflow",
        doc={"a": INT32_MAX, "b": -1},
        expression={"$subtract": ["$a", "$b"]},
        expected=Int64(INT32_OVERFLOW),
        msg="$subtract should promote to int64 when the int32 result exceeds INT32_MAX",
    ),
    ExpressionTestCase(
        "int32_underflow",
        doc={"a": INT32_MIN, "b": 1},
        expression={"$subtract": ["$a", "$b"]},
        expected=Int64(INT32_UNDERFLOW),
        msg="$subtract should promote to int64 when the int32 result is below INT32_MIN",
    ),
    # Int32 boundary values
    ExpressionTestCase(
        "int32_max_minuend",
        doc={"a": INT32_MAX, "b": 10},
        expression={"$subtract": ["$a", "$b"]},
        expected=2147483637,
        msg="$subtract should correctly subtract from INT32_MAX",
    ),
    ExpressionTestCase(
        "int32_max_minus_1_minuend",
        doc={"a": INT32_MAX_MINUS_1, "b": 10},
        expression={"$subtract": ["$a", "$b"]},
        expected=2147483636,
        msg="$subtract should correctly subtract from INT32_MAX - 1",
    ),
    ExpressionTestCase(
        "int32_min_minuend",
        doc={"a": INT32_MIN, "b": 10},
        expression={"$subtract": ["$a", "$b"]},
        expected=Int64(-2147483658),
        msg="$subtract should promote to int64 when subtracting from INT32_MIN",
    ),
    ExpressionTestCase(
        "int32_min_plus_1_minuend",
        doc={"a": INT32_MIN_PLUS_1, "b": 10},
        expression={"$subtract": ["$a", "$b"]},
        expected=Int64(-2147483657),
        msg="$subtract should promote to int64 when subtracting from INT32_MIN + 1",
    ),
    ExpressionTestCase(
        "int32_max_subtrahend",
        doc={"a": 10, "b": INT32_MAX},
        expression={"$subtract": ["$a", "$b"]},
        expected=-2147483637,
        msg="$subtract should correctly subtract INT32_MAX as the subtrahend",
    ),
    ExpressionTestCase(
        "int32_min_subtrahend",
        doc={"a": 10, "b": INT32_MIN},
        expression={"$subtract": ["$a", "$b"]},
        expected=Int64(2147483658),
        msg="$subtract should promote to int64 when INT32_MIN is the subtrahend",
    ),
    # Int64 overflow and underflow
    ExpressionTestCase(
        "int64_overflow",
        doc={"a": INT64_MAX, "b": -1},
        expression={"$subtract": ["$a", "$b"]},
        expected=9.223372036854776e18,
        msg="$subtract should promote to double when the int64 result exceeds INT64_MAX",
    ),
    ExpressionTestCase(
        "int64_underflow",
        doc={"a": INT64_MIN, "b": 1},
        expression={"$subtract": ["$a", "$b"]},
        expected=-9.223372036854776e18,
        msg="$subtract should promote to double when the int64 result is below INT64_MIN",
    ),
    # Int64 boundary values
    ExpressionTestCase(
        "int64_max_minuend",
        doc={"a": INT64_MAX, "b": Int64(10)},
        expression={"$subtract": ["$a", "$b"]},
        expected=Int64(9223372036854775797),
        msg="$subtract should correctly subtract from INT64_MAX",
    ),
    ExpressionTestCase(
        "int64_max_minus_1_minuend",
        doc={"a": INT64_MAX_MINUS_1, "b": Int64(10)},
        expression={"$subtract": ["$a", "$b"]},
        expected=Int64(9223372036854775796),
        msg="$subtract should correctly subtract from INT64_MAX - 1",
    ),
    ExpressionTestCase(
        "int64_min_minuend",
        doc={"a": INT64_MIN, "b": Int64(10)},
        expression={"$subtract": ["$a", "$b"]},
        expected=-9.223372036854776e18,
        msg="$subtract should overflow to double when subtracting from INT64_MIN",
    ),
    ExpressionTestCase(
        "int64_min_plus_1_minuend",
        doc={"a": INT64_MIN_PLUS_1, "b": Int64(10)},
        expression={"$subtract": ["$a", "$b"]},
        expected=-9.223372036854776e18,
        msg="$subtract should overflow to double when subtracting from INT64_MIN + 1",
    ),
    ExpressionTestCase(
        "int64_max_subtrahend",
        doc={"a": Int64(10), "b": INT64_MAX},
        expression={"$subtract": ["$a", "$b"]},
        expected=Int64(-9223372036854775797),
        msg="$subtract should correctly subtract INT64_MAX as the subtrahend",
    ),
    ExpressionTestCase(
        "int64_min_subtrahend",
        doc={"a": Int64(10), "b": INT64_MIN},
        expression={"$subtract": ["$a", "$b"]},
        expected=9.223372036854776e18,
        msg="$subtract should overflow to double when INT64_MIN is the subtrahend",
    ),
    # Double overflow
    ExpressionTestCase(
        "double_overflow",
        doc={"a": 1e308, "b": -1e308},
        expression={"$subtract": ["$a", "$b"]},
        expected=FLOAT_INFINITY,
        msg="$subtract should return Infinity on double overflow",
    ),
    ExpressionTestCase(
        "double_underflow",
        doc={"a": -1e308, "b": 1e308},
        expression={"$subtract": ["$a", "$b"]},
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$subtract should return -Infinity on double underflow",
    ),
    # Double boundary values
    ExpressionTestCase(
        "double_min_subnormal_minuend",
        doc={"a": DOUBLE_MIN_SUBNORMAL, "b": 0},
        expression={"$subtract": ["$a", "$b"]},
        expected=5e-324,
        msg="$subtract should handle the minimum subnormal double value",
    ),
    ExpressionTestCase(
        "double_near_min_minuend",
        doc={"a": DOUBLE_NEAR_MIN, "b": 0},
        expression={"$subtract": ["$a", "$b"]},
        expected=1e-308,
        msg="$subtract should handle doubles near the minimum normal value",
    ),
    ExpressionTestCase(
        "double_near_max_minuend",
        doc={"a": DOUBLE_NEAR_MAX, "b": 1e307},
        expression={"$subtract": ["$a", "$b"]},
        expected=9e307,
        msg="$subtract should handle doubles near the maximum value",
    ),
    ExpressionTestCase(
        "double_max_safe_integer_minuend",
        doc={"a": float(DOUBLE_MAX_SAFE_INTEGER), "b": 1},
        expression={"$subtract": ["$a", "$b"]},
        expected=9007199254740991.0,
        msg="$subtract should handle the maximum safe integer double as the minuend",
    ),
    ExpressionTestCase(
        "double_max_safe_integer_subtrahend",
        doc={"a": 1, "b": float(DOUBLE_MAX_SAFE_INTEGER)},
        expression={"$subtract": ["$a", "$b"]},
        expected=-9007199254740991.0,
        msg="$subtract should handle the maximum safe integer double as the subtrahend",
    ),
    # Decimal128 boundary values
    ExpressionTestCase(
        "decimal128_max_minuend",
        doc={"a": DECIMAL128_MAX, "b": Decimal128("1")},
        expression={"$subtract": ["$a", "$b"]},
        expected=DECIMAL128_MAX,
        msg="$subtract should handle DECIMAL128_MAX as the minuend",
    ),
    ExpressionTestCase(
        "decimal128_min_minuend",
        doc={"a": DECIMAL128_MIN, "b": Decimal128("1")},
        expression={"$subtract": ["$a", "$b"]},
        expected=DECIMAL128_MIN,
        msg="$subtract should handle DECIMAL128_MIN as the minuend",
    ),
    ExpressionTestCase(
        "decimal128_small_exponent_minuend",
        doc={"a": DECIMAL128_SMALL_EXPONENT, "b": Decimal128("0")},
        expression={"$subtract": ["$a", "$b"]},
        expected=DECIMAL128_SMALL_EXPONENT,
        msg="$subtract should handle Decimal128 with a small exponent",
    ),
    ExpressionTestCase(
        "decimal128_large_exponent_minuend",
        doc={"a": DECIMAL128_LARGE_EXPONENT, "b": Decimal128("1")},
        expression={"$subtract": ["$a", "$b"]},
        expected=DECIMAL128_LARGE_EXPONENT,
        msg="$subtract should handle Decimal128 with a large exponent",
    ),
    ExpressionTestCase(
        "decimal128_trailing_zero",
        doc={"a": DECIMAL128_TRAILING_ZERO, "b": Decimal128("0.5")},
        expression={"$subtract": ["$a", "$b"]},
        expected=Decimal128("0.5"),
        msg="$subtract should handle Decimal128 with a trailing zero",
    ),
    ExpressionTestCase(
        "decimal128_many_trailing_zeros",
        doc={"a": DECIMAL128_MANY_TRAILING_ZEROS, "b": Decimal128("0.5")},
        expression={"$subtract": ["$a", "$b"]},
        expected=Decimal128("0.50000000000000000000000000000000"),
        msg="$subtract should handle Decimal128 with many trailing zeros",
    ),
    # Decimal128 precision
    ExpressionTestCase(
        "decimal_precision",
        doc={"a": Decimal128("10.5"), "b": Decimal128("2.5")},
        expression={"$subtract": ["$a", "$b"]},
        expected=Decimal128("8.0"),
        msg="$subtract should preserve Decimal128 precision",
    ),
    ExpressionTestCase(
        "decimal_precision_small",
        doc={"a": Decimal128("0.3"), "b": Decimal128("0.1")},
        expression={"$subtract": ["$a", "$b"]},
        expected=Decimal128("0.2"),
        msg="$subtract should compute 0.3 - 0.1 exactly in Decimal128 without floating-point error",
    ),
    ExpressionTestCase(
        "decimal_large_precision",
        doc={
            "a": Decimal128("1000000000000000000000000000000000"),
            "b": Decimal128("1"),
        },
        expression={"$subtract": ["$a", "$b"]},
        expected=Decimal128("999999999999999999999999999999999"),
        msg="$subtract should handle large Decimal128 values with full precision",
    ),
    # Double rounding edge cases
    ExpressionTestCase(
        "double_half_minuend",
        doc={"a": DOUBLE_HALF, "b": 0.25},
        expression={"$subtract": ["$a", "$b"]},
        expected=0.25,
        msg="$subtract should correctly compute 0.5 - 0.25 = 0.25",
    ),
    ExpressionTestCase(
        "double_one_and_half_minuend",
        doc={"a": DOUBLE_ONE_AND_HALF, "b": 0.5},
        expression={"$subtract": ["$a", "$b"]},
        expected=1.0,
        msg="$subtract should correctly compute 1.5 - 0.5 = 1.0",
    ),
    ExpressionTestCase(
        "double_two_and_half_minuend",
        doc={"a": DOUBLE_TWO_AND_HALF, "b": 1.5},
        expression={"$subtract": ["$a", "$b"]},
        expected=1.0,
        msg="$subtract should correctly compute 2.5 - 1.5 = 1.0",
    ),
    ExpressionTestCase(
        "double_negative_half_minuend",
        doc={"a": DOUBLE_NEGATIVE_HALF, "b": 0.5},
        expression={"$subtract": ["$a", "$b"]},
        expected=-1.0,
        msg="$subtract should correctly compute -0.5 - 0.5 = -1.0",
    ),
    ExpressionTestCase(
        "double_negative_one_and_half_minuend",
        doc={"a": DOUBLE_NEGATIVE_ONE_AND_HALF, "b": 0.5},
        expression={"$subtract": ["$a", "$b"]},
        expected=-2.0,
        msg="$subtract should correctly compute -1.5 - 0.5 = -2.0",
    ),
    ExpressionTestCase(
        "double_just_below_half_minuend",
        doc={"a": DOUBLE_JUST_BELOW_HALF, "b": 0.25},
        expression={"$subtract": ["$a", "$b"]},
        expected=pytest.approx(0.2499999999999994),
        msg="$subtract should handle a double just below 0.5",
    ),
    ExpressionTestCase(
        "double_just_above_half_minuend",
        doc={"a": DOUBLE_JUST_ABOVE_HALF, "b": 0.25},
        expression={"$subtract": ["$a", "$b"]},
        expected=pytest.approx(0.250000001),
        msg="$subtract should handle a double just above 0.5",
    ),
    # Decimal128 rounding edge cases
    ExpressionTestCase(
        "decimal_half_minuend",
        doc={"a": DECIMAL128_HALF, "b": Decimal128("0.25")},
        expression={"$subtract": ["$a", "$b"]},
        expected=Decimal128("0.25"),
        msg="$subtract should correctly compute Decimal128 0.5 - 0.25 = 0.25",
    ),
    ExpressionTestCase(
        "decimal_one_and_half_minuend",
        doc={"a": DECIMAL128_ONE_AND_HALF, "b": Decimal128("0.5")},
        expression={"$subtract": ["$a", "$b"]},
        expected=Decimal128("1.0"),
        msg="$subtract should correctly compute Decimal128 1.5 - 0.5 = 1.0",
    ),
    ExpressionTestCase(
        "decimal_two_and_half_minuend",
        doc={"a": DECIMAL128_TWO_AND_HALF, "b": Decimal128("1.5")},
        expression={"$subtract": ["$a", "$b"]},
        expected=Decimal128("1.0"),
        msg="$subtract should correctly compute Decimal128 2.5 - 1.5 = 1.0",
    ),
    ExpressionTestCase(
        "decimal_negative_half_minuend",
        doc={"a": DECIMAL128_NEGATIVE_HALF, "b": Decimal128("0.5")},
        expression={"$subtract": ["$a", "$b"]},
        expected=Decimal128("-1.0"),
        msg="$subtract should correctly compute Decimal128 -0.5 - 0.5 = -1.0",
    ),
    ExpressionTestCase(
        "decimal_negative_one_and_half_minuend",
        doc={"a": DECIMAL128_NEGATIVE_ONE_AND_HALF, "b": Decimal128("0.5")},
        expression={"$subtract": ["$a", "$b"]},
        expected=Decimal128("-2.0"),
        msg="$subtract should correctly compute Decimal128 -1.5 - 0.5 = -2.0",
    ),
    ExpressionTestCase(
        "decimal_just_below_half_minuend",
        doc={"a": DECIMAL128_JUST_BELOW_HALF, "b": Decimal128("0.25")},
        expression={"$subtract": ["$a", "$b"]},
        expected=Decimal128("0.2499999999999999999999999999999999"),
        msg="$subtract should handle Decimal128 just below 0.5",
    ),
    ExpressionTestCase(
        "decimal_just_above_half_minuend",
        doc={"a": DECIMAL128_JUST_ABOVE_HALF, "b": Decimal128("0.25")},
        expression={"$subtract": ["$a", "$b"]},
        expected=Decimal128("0.2500000000000000000000000000000001"),
        msg="$subtract should handle Decimal128 just above 0.5",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(SUBTRACT_BOUNDARY_TESTS))
def test_subtract_boundaries(collection, test_case: ExpressionTestCase):
    """Test $subtract boundary values, overflow behavior, and numeric precision."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
