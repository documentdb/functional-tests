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
    DECIMAL128_INT64_OVERFLOW,
    DECIMAL128_INT64_UNDERFLOW,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MAX,
    DECIMAL128_MAX_COEFFICIENT,
    DECIMAL128_MAX_NEGATIVE,
    DECIMAL128_MIN,
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_SMALL_EXPONENT,
    DECIMAL128_ZERO,
    DOUBLE_FROM_INT64_MAX,
    DOUBLE_MAX,
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_MIN,
    DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    DOUBLE_NEAR_MIN,
    DOUBLE_PRECISION_LOSS,
    DOUBLE_ZERO,
    INT32_MAX,
    INT32_MIN,
    INT32_OVERFLOW,
    INT32_UNDERFLOW,
    INT64_MAX,
    INT64_MIN,
)

# Property [Integer Boundary Behavior]: numeric comparison is correct at
# type-width boundaries where values cross from int32 to int64 to Decimal128.
MAX_INTEGER_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    # Cross-type: int32 boundary to int64.
    ExpressionTestCase(
        "intbound_int32_min_vs_int64_underflow",
        expression={"$max": ["$a", "$b"]},
        doc={"a": INT32_MIN, "b": INT32_UNDERFLOW},
        expected=INT32_MIN,
        msg="$max should pick int32 min over the int64 value just below it",
    ),
    # Cross-type: int64 boundary to Decimal128.
    ExpressionTestCase(
        "intbound_int64_max_vs_decimal128_overflow",
        expression={"$max": ["$a", "$b"]},
        doc={"a": INT64_MAX, "b": DECIMAL128_INT64_OVERFLOW},
        expected=DECIMAL128_INT64_OVERFLOW,
        msg="$max should pick Decimal128 int64 overflow over int64 max",
    ),
    ExpressionTestCase(
        "intbound_int64_min_vs_decimal128_underflow",
        expression={"$max": ["$a", "$b"]},
        doc={"a": INT64_MIN, "b": DECIMAL128_INT64_UNDERFLOW},
        expected=INT64_MIN,
        msg="$max should pick int64 min over Decimal128 int64 underflow",
    ),
    # Reversed order: verify $max does not just return the last element.
    ExpressionTestCase(
        "intbound_decimal128_overflow_vs_int64_max",
        expression={"$max": ["$a", "$b"]},
        doc={"a": DECIMAL128_INT64_OVERFLOW, "b": INT64_MAX},
        expected=DECIMAL128_INT64_OVERFLOW,
        msg="$max should pick Decimal128 int64 overflow over int64 max regardless of order",
    ),
]

# Property [Float Boundary Behavior]: extreme and special double values
# participate correctly in numeric comparison.
MAX_FLOAT_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    # Subnormal values participate in comparison.
    ExpressionTestCase(
        "floatbound_subnormal_vs_zero",
        expression={"$max": ["$a", "$b"]},
        doc={"a": DOUBLE_MIN_SUBNORMAL, "b": DOUBLE_ZERO},
        expected=DOUBLE_MIN_SUBNORMAL,
        msg="$max should pick positive subnormal over zero",
    ),
    ExpressionTestCase(
        "floatbound_neg_subnormal_vs_zero",
        expression={"$max": ["$a", "$b"]},
        doc={"a": DOUBLE_MIN_NEGATIVE_SUBNORMAL, "b": DOUBLE_ZERO},
        expected=DOUBLE_ZERO,
        msg="$max should pick zero over negative subnormal",
    ),
    ExpressionTestCase(
        "floatbound_subnormal_vs_neg_subnormal",
        expression={"$max": ["$a", "$b"]},
        doc={"a": DOUBLE_MIN_SUBNORMAL, "b": DOUBLE_MIN_NEGATIVE_SUBNORMAL},
        expected=DOUBLE_MIN_SUBNORMAL,
        msg="$max should pick positive subnormal over negative subnormal",
    ),
    # Near-boundary doubles.
    ExpressionTestCase(
        "floatbound_near_max_vs_near_min",
        expression={"$max": ["$a", "$b"]},
        doc={"a": DOUBLE_NEAR_MAX, "b": DOUBLE_NEAR_MIN},
        expected=DOUBLE_NEAR_MAX,
        msg="$max should pick the larger near-boundary double",
    ),
    ExpressionTestCase(
        "floatbound_dbl_max_vs_near_max",
        expression={"$max": ["$a", "$b"]},
        doc={"a": DOUBLE_MAX, "b": DOUBLE_NEAR_MAX},
        expected=DOUBLE_MAX,
        msg="$max should pick DBL_MAX over 1e308",
    ),
    ExpressionTestCase(
        "floatbound_dbl_min_vs_near_max",
        expression={"$max": ["$a", "$b"]},
        doc={"a": DOUBLE_MIN, "b": DOUBLE_NEAR_MAX},
        expected=DOUBLE_NEAR_MAX,
        msg="$max should pick 1e308 over -DBL_MAX",
    ),
    # Max safe integer and precision-loss integer.
    ExpressionTestCase(
        "floatbound_safe_int_vs_precision_loss",
        expression={"$max": ["$a", "$b"]},
        doc={"a": DOUBLE_MAX_SAFE_INTEGER, "b": DOUBLE_MAX_SAFE_INTEGER + 1},
        expected=Int64(DOUBLE_MAX_SAFE_INTEGER + 1),
        msg="$max should pick precision-loss integer over max safe integer",
    ),
    ExpressionTestCase(
        "floatbound_int64_precision_loss_vs_safe_int",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Int64(DOUBLE_PRECISION_LOSS), "b": float(DOUBLE_MAX_SAFE_INTEGER)},
        expected=Int64(DOUBLE_PRECISION_LOSS),
        msg="$max should pick Int64 at precision boundary over max safe integer as float",
    ),
    # IEEE 754 imprecise value (0.1).
    ExpressionTestCase(
        "floatbound_imprecise_vs_zero",
        expression={"$max": ["$a", "$b"]},
        doc={"a": 0.1, "b": DOUBLE_ZERO},
        expected=0.1,
        msg="$max should pick IEEE 754 imprecise value over zero",
    ),
    # INT64_MAX as double rounds up due to IEEE 754, so it is greater.
    ExpressionTestCase(
        "floatbound_double_int64_max_vs_int64_max",
        expression={"$max": ["$a", "$b"]},
        doc={"a": DOUBLE_FROM_INT64_MAX, "b": INT64_MAX},
        expected=DOUBLE_FROM_INT64_MAX,
        msg=(
            "$max should pick double representation of INT64_MAX over"
            " Int64 max because IEEE 754 rounds it up"
        ),
    ),
    ExpressionTestCase(
        "floatbound_int64_max_vs_double_int64_max",
        expression={"$max": ["$a", "$b"]},
        doc={"a": INT64_MAX, "b": DOUBLE_FROM_INT64_MAX},
        expected=DOUBLE_FROM_INT64_MAX,
        msg=(
            "$max should pick double representation of INT64_MAX over"
            " Int64 max regardless of order"
        ),
    ),
]

# Property [Decimal128 Boundary Behavior]: extreme Decimal128 values
# participate correctly in numeric comparison.
MAX_DECIMAL128_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "dec128bound_zero_vs_positive",
        expression={"$max": ["$a", "$b"]},
        doc={"a": DECIMAL128_ZERO, "b": Decimal128("1")},
        expected=Decimal128("1"),
        msg="$max should pick positive Decimal128 over Decimal128 zero",
    ),
    ExpressionTestCase(
        "dec128bound_negzero_vs_positive",
        expression={"$max": ["$a", "$b"]},
        doc={"a": DECIMAL128_NEGATIVE_ZERO, "b": Decimal128("1")},
        expected=Decimal128("1"),
        msg="$max should pick positive Decimal128 over Decimal128 negative zero",
    ),
    ExpressionTestCase(
        "dec128bound_trailing_zero_vs_int",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Decimal128("3.0"), "b": 5},
        expected=5,
        msg="$max should compare Decimal128 with trailing zero numerically",
    ),
    ExpressionTestCase(
        "dec128bound_many_trailing_zeros_vs_int",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Decimal128("3.00000000000000000000000000000000"), "b": 5},
        expected=5,
        msg="$max should compare Decimal128 with many trailing zeros numerically",
    ),
    ExpressionTestCase(
        "dec128bound_max_coefficient_vs_int64_max",
        expression={"$max": ["$a", "$b"]},
        doc={"a": DECIMAL128_MAX_COEFFICIENT, "b": INT64_MAX},
        expected=DECIMAL128_MAX_COEFFICIENT,
        msg="$max should pick 34-digit max coefficient over int64 max",
    ),
    ExpressionTestCase(
        "dec128bound_34_digit_precision",
        expression={"$max": ["$a", "$b"]},
        doc={
            "a": Decimal128("1234567890123456789012345678901235"),
            "b": Decimal128("1234567890123456789012345678901234"),
        },
        expected=Decimal128("1234567890123456789012345678901235"),
        msg="$max should compare 34-digit Decimal128 values without truncation",
    ),
    ExpressionTestCase(
        "dec128bound_large_exponent_vs_max",
        expression={"$max": ["$a", "$b"]},
        doc={"a": DECIMAL128_LARGE_EXPONENT, "b": DECIMAL128_MAX},
        expected=DECIMAL128_MAX,
        msg="$max should pick Decimal128 MAX over 1E+6144",
    ),
    ExpressionTestCase(
        "dec128bound_small_exponent_vs_zero",
        expression={"$max": ["$a", "$b"]},
        doc={"a": DECIMAL128_SMALL_EXPONENT, "b": DECIMAL128_ZERO},
        expected=DECIMAL128_SMALL_EXPONENT,
        msg="$max should pick 1E-6143 over Decimal128 zero",
    ),
    ExpressionTestCase(
        "dec128bound_min_positive_vs_zero",
        expression={"$max": ["$a", "$b"]},
        doc={"a": DECIMAL128_MIN_POSITIVE, "b": DECIMAL128_ZERO},
        expected=DECIMAL128_MIN_POSITIVE,
        msg="$max should pick smallest positive Decimal128 1E-6176 over zero",
    ),
    ExpressionTestCase(
        "dec128bound_max_negative_vs_zero",
        expression={"$max": ["$a", "$b"]},
        doc={"a": DECIMAL128_MAX_NEGATIVE, "b": DECIMAL128_ZERO},
        expected=DECIMAL128_ZERO,
        msg="$max should pick zero over largest negative Decimal128 -1E-6176",
    ),
    ExpressionTestCase(
        "dec128bound_min_positive_vs_max_negative",
        expression={"$max": ["$a", "$b"]},
        doc={"a": DECIMAL128_MIN_POSITIVE, "b": DECIMAL128_MAX_NEGATIVE},
        expected=DECIMAL128_MIN_POSITIVE,
        msg="$max should pick 1E-6176 over -1E-6176",
    ),
    ExpressionTestCase(
        "dec128bound_max_vs_min",
        expression={"$max": ["$a", "$b"]},
        doc={"a": DECIMAL128_MAX, "b": DECIMAL128_MIN},
        expected=DECIMAL128_MAX,
        msg="$max should pick Decimal128 MAX over Decimal128 MIN",
    ),
]

# Property [Integer Boundary Type Promotion]: when the larger value at a
# type-width boundary is a wider integer type, the result has that wider type.
MAX_INTEGER_BOUNDARY_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "intbound_int32_max_vs_int64_overflow",
        expression={
            "$let": {"vars": {"m": {"$max": ["$a", "$b"]}}, "in": [{"$type": "$$m"}, "$$m"]}
        },
        doc={"a": INT32_MAX, "b": INT32_OVERFLOW},
        expected=["long", Int64(INT32_OVERFLOW)],
        msg="$max should return int64 type when int64 value just above int32 max wins",
    ),
    ExpressionTestCase(
        "intbound_int64_overflow_vs_int32_max",
        expression={
            "$let": {"vars": {"m": {"$max": ["$a", "$b"]}}, "in": [{"$type": "$$m"}, "$$m"]}
        },
        doc={"a": INT32_OVERFLOW, "b": INT32_MAX},
        expected=["long", Int64(INT32_OVERFLOW)],
        msg=(
            "$max should return int64 type when int64 value just above"
            " int32 max wins regardless of order"
        ),
    ),
]

MAX_NUMERIC_BOUNDARY_TESTS = (
    MAX_INTEGER_BOUNDARY_TESTS
    + MAX_FLOAT_BOUNDARY_TESTS
    + MAX_DECIMAL128_BOUNDARY_TESTS
    + MAX_INTEGER_BOUNDARY_TYPE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(MAX_NUMERIC_BOUNDARY_TESTS))
def test_max_numeric_boundary_cases(collection, test_case: ExpressionTestCase):
    """Test $max numeric boundary cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc or {})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
