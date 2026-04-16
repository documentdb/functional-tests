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
    INT32_MIN,
    INT32_UNDERFLOW,
    INT64_MAX,
    INT64_MIN,
)

# Property [Integer Boundary Behavior]: numeric comparison is correct at
# type-width boundaries where values cross from int32 to int64 to Decimal128.
MIN_INTEGER_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    # Cross-type: int32 boundary to int64.
    ExpressionTestCase(
        "intbound_int32_min_vs_int64_underflow",
        expression={"$min": ["$a", "$b"]},
        doc={"a": INT32_MIN, "b": INT32_UNDERFLOW},
        expected=Int64(INT32_UNDERFLOW),
        msg="$min should pick the int64 value just below int32 min over int32 min",
    ),
    # Cross-type: int64 boundary to Decimal128.
    ExpressionTestCase(
        "intbound_int64_max_vs_decimal128_overflow",
        expression={"$min": ["$a", "$b"]},
        doc={"a": INT64_MAX, "b": DECIMAL128_INT64_OVERFLOW},
        expected=INT64_MAX,
        msg="$min should pick int64 max over Decimal128 int64 overflow",
    ),
    ExpressionTestCase(
        "intbound_int64_min_vs_decimal128_underflow",
        expression={"$min": ["$a", "$b"]},
        doc={"a": INT64_MIN, "b": DECIMAL128_INT64_UNDERFLOW},
        expected=DECIMAL128_INT64_UNDERFLOW,
        msg="$min should pick Decimal128 int64 underflow over int64 min",
    ),
    # Reversed order: verify $min does not just return the first element.
    ExpressionTestCase(
        "intbound_decimal128_overflow_vs_int64_max",
        expression={"$min": ["$a", "$b"]},
        doc={"a": DECIMAL128_INT64_OVERFLOW, "b": INT64_MAX},
        expected=INT64_MAX,
        msg="$min should pick int64 max over Decimal128 int64 overflow regardless of order",
    ),
]

# Property [Float Boundary Behavior]: extreme and special double values
# participate correctly in numeric comparison.
MIN_FLOAT_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    # Subnormal values participate in comparison.
    ExpressionTestCase(
        "floatbound_subnormal_vs_zero",
        expression={"$min": ["$a", "$b"]},
        doc={"a": DOUBLE_MIN_SUBNORMAL, "b": DOUBLE_ZERO},
        expected=DOUBLE_ZERO,
        msg="$min should pick zero over positive subnormal",
    ),
    ExpressionTestCase(
        "floatbound_neg_subnormal_vs_zero",
        expression={"$min": ["$a", "$b"]},
        doc={"a": DOUBLE_MIN_NEGATIVE_SUBNORMAL, "b": DOUBLE_ZERO},
        expected=DOUBLE_MIN_NEGATIVE_SUBNORMAL,
        msg="$min should pick negative subnormal over zero",
    ),
    ExpressionTestCase(
        "floatbound_subnormal_vs_neg_subnormal",
        expression={"$min": ["$a", "$b"]},
        doc={"a": DOUBLE_MIN_SUBNORMAL, "b": DOUBLE_MIN_NEGATIVE_SUBNORMAL},
        expected=DOUBLE_MIN_NEGATIVE_SUBNORMAL,
        msg="$min should pick negative subnormal over positive subnormal",
    ),
    # Near-boundary doubles.
    ExpressionTestCase(
        "floatbound_near_max_vs_near_min",
        expression={"$min": ["$a", "$b"]},
        doc={"a": DOUBLE_NEAR_MAX, "b": DOUBLE_NEAR_MIN},
        expected=DOUBLE_NEAR_MIN,
        msg="$min should pick the smaller near-boundary double",
    ),
    ExpressionTestCase(
        "floatbound_dbl_max_vs_near_max",
        expression={"$min": ["$a", "$b"]},
        doc={"a": DOUBLE_MAX, "b": DOUBLE_NEAR_MAX},
        expected=DOUBLE_NEAR_MAX,
        msg="$min should pick 1e308 over DBL_MAX",
    ),
    ExpressionTestCase(
        "floatbound_dbl_min_vs_near_max",
        expression={"$min": ["$a", "$b"]},
        doc={"a": DOUBLE_MIN, "b": DOUBLE_NEAR_MAX},
        expected=DOUBLE_MIN,
        msg="$min should pick -DBL_MAX over 1e308",
    ),
    # Max safe integer and precision-loss integer.
    ExpressionTestCase(
        "floatbound_safe_int_vs_precision_loss",
        expression={"$min": ["$a", "$b"]},
        doc={"a": DOUBLE_MAX_SAFE_INTEGER, "b": DOUBLE_MAX_SAFE_INTEGER + 1},
        expected=Int64(DOUBLE_MAX_SAFE_INTEGER),
        msg="$min should pick max safe integer over precision-loss integer",
    ),
    ExpressionTestCase(
        "floatbound_int64_precision_loss_vs_safe_int",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Int64(DOUBLE_PRECISION_LOSS), "b": float(DOUBLE_MAX_SAFE_INTEGER)},
        expected=float(DOUBLE_MAX_SAFE_INTEGER),
        msg="$min should pick max safe integer as float over Int64 at precision boundary",
    ),
    # IEEE 754 imprecise value (0.1).
    ExpressionTestCase(
        "floatbound_imprecise_vs_zero",
        expression={"$min": ["$a", "$b"]},
        doc={"a": 0.1, "b": DOUBLE_ZERO},
        expected=DOUBLE_ZERO,
        msg="$min should pick zero over IEEE 754 imprecise value",
    ),
    # INT64_MAX as double rounds up due to IEEE 754, so it is greater.
    ExpressionTestCase(
        "floatbound_double_int64_max_vs_int64_max",
        expression={"$min": ["$a", "$b"]},
        doc={"a": DOUBLE_FROM_INT64_MAX, "b": INT64_MAX},
        expected=INT64_MAX,
        msg=(
            "$min should pick Int64 max over double representation of"
            " INT64_MAX because IEEE 754 rounds it up"
        ),
    ),
    ExpressionTestCase(
        "floatbound_int64_max_vs_double_int64_max",
        expression={"$min": ["$a", "$b"]},
        doc={"a": INT64_MAX, "b": DOUBLE_FROM_INT64_MAX},
        expected=INT64_MAX,
        msg=(
            "$min should pick Int64 max over double"
            " representation of INT64_MAX regardless of order"
        ),
    ),
]

# Property [Decimal128 Boundary Behavior]: extreme Decimal128 values
# participate correctly in numeric comparison.
MIN_DECIMAL128_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "dec128bound_zero_vs_positive",
        expression={"$min": ["$a", "$b"]},
        doc={"a": DECIMAL128_ZERO, "b": Decimal128("1")},
        expected=DECIMAL128_ZERO,
        msg="$min should pick Decimal128 zero over positive Decimal128",
    ),
    ExpressionTestCase(
        "dec128bound_negzero_vs_positive",
        expression={"$min": ["$a", "$b"]},
        doc={"a": DECIMAL128_NEGATIVE_ZERO, "b": Decimal128("1")},
        expected=DECIMAL128_NEGATIVE_ZERO,
        msg="$min should pick Decimal128 negative zero over positive Decimal128",
    ),
    ExpressionTestCase(
        "dec128bound_trailing_zero_vs_int",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Decimal128("3.0"), "b": 5},
        expected=Decimal128("3.0"),
        msg="$min should compare Decimal128 with trailing zero numerically",
    ),
    ExpressionTestCase(
        "dec128bound_many_trailing_zeros_vs_int",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Decimal128("3.00000000000000000000000000000000"), "b": 5},
        expected=Decimal128("3.00000000000000000000000000000000"),
        msg="$min should compare Decimal128 with many trailing zeros numerically",
    ),
    ExpressionTestCase(
        "dec128bound_max_coefficient_vs_int64_max",
        expression={"$min": ["$a", "$b"]},
        doc={"a": DECIMAL128_MAX_COEFFICIENT, "b": INT64_MAX},
        expected=INT64_MAX,
        msg="$min should pick int64 max over 34-digit max coefficient",
    ),
    ExpressionTestCase(
        "dec128bound_34_digit_precision",
        expression={"$min": ["$a", "$b"]},
        doc={
            "a": Decimal128("1234567890123456789012345678901235"),
            "b": Decimal128("1234567890123456789012345678901234"),
        },
        expected=Decimal128("1234567890123456789012345678901234"),
        msg="$min should compare 34-digit Decimal128 values without truncation",
    ),
    ExpressionTestCase(
        "dec128bound_large_exponent_vs_max",
        expression={"$min": ["$a", "$b"]},
        doc={"a": DECIMAL128_LARGE_EXPONENT, "b": DECIMAL128_MAX},
        expected=DECIMAL128_LARGE_EXPONENT,
        msg="$min should pick 1E+6144 over Decimal128 MAX",
    ),
    ExpressionTestCase(
        "dec128bound_small_exponent_vs_zero",
        expression={"$min": ["$a", "$b"]},
        doc={"a": DECIMAL128_SMALL_EXPONENT, "b": DECIMAL128_ZERO},
        expected=DECIMAL128_ZERO,
        msg="$min should pick Decimal128 zero over 1E-6143",
    ),
    ExpressionTestCase(
        "dec128bound_min_positive_vs_zero",
        expression={"$min": ["$a", "$b"]},
        doc={"a": DECIMAL128_MIN_POSITIVE, "b": DECIMAL128_ZERO},
        expected=DECIMAL128_ZERO,
        msg="$min should pick zero over smallest positive Decimal128 1E-6176",
    ),
    ExpressionTestCase(
        "dec128bound_max_negative_vs_zero",
        expression={"$min": ["$a", "$b"]},
        doc={"a": DECIMAL128_MAX_NEGATIVE, "b": DECIMAL128_ZERO},
        expected=DECIMAL128_MAX_NEGATIVE,
        msg="$min should pick largest negative Decimal128 -1E-6176 over zero",
    ),
    ExpressionTestCase(
        "dec128bound_min_positive_vs_max_negative",
        expression={"$min": ["$a", "$b"]},
        doc={"a": DECIMAL128_MIN_POSITIVE, "b": DECIMAL128_MAX_NEGATIVE},
        expected=DECIMAL128_MAX_NEGATIVE,
        msg="$min should pick -1E-6176 over 1E-6176",
    ),
    ExpressionTestCase(
        "dec128bound_max_vs_min",
        expression={"$min": ["$a", "$b"]},
        doc={"a": DECIMAL128_MAX, "b": DECIMAL128_MIN},
        expected=DECIMAL128_MIN,
        msg="$min should pick Decimal128 MIN over Decimal128 MAX",
    ),
]

# Property [Integer Boundary Type Promotion]: when the smaller value at a
# type-width boundary is a wider integer type, the result has that wider type.
MIN_INTEGER_BOUNDARY_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "intbound_int32_min_vs_int64_underflow",
        expression={
            "$let": {"vars": {"m": {"$min": ["$a", "$b"]}}, "in": [{"$type": "$$m"}, "$$m"]}
        },
        doc={"a": INT32_MIN, "b": INT32_UNDERFLOW},
        expected=["long", Int64(INT32_UNDERFLOW)],
        msg="$min should return int64 type when int64 value just below int32 min wins",
    ),
    ExpressionTestCase(
        "intbound_int64_underflow_vs_int32_min",
        expression={
            "$let": {"vars": {"m": {"$min": ["$a", "$b"]}}, "in": [{"$type": "$$m"}, "$$m"]}
        },
        doc={"a": INT32_UNDERFLOW, "b": INT32_MIN},
        expected=["long", Int64(INT32_UNDERFLOW)],
        msg=(
            "$min should return int64 type when int64 value just below"
            " int32 min wins regardless of order"
        ),
    ),
]

MIN_NUMERIC_BOUNDARY_TESTS = (
    MIN_INTEGER_BOUNDARY_TESTS
    + MIN_FLOAT_BOUNDARY_TESTS
    + MIN_DECIMAL128_BOUNDARY_TESTS
    + MIN_INTEGER_BOUNDARY_TYPE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(MIN_NUMERIC_BOUNDARY_TESTS))
def test_min_numeric_boundary_cases(collection, test_case: ExpressionTestCase):
    """Test $min numeric boundary cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc or {})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
