from __future__ import annotations

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MAX,
    DECIMAL128_MAX_COEFFICIENT,
    DECIMAL128_MAX_NEGATIVE,
    DECIMAL128_MIN,
    DECIMAL128_MIN_COEFFICIENT,
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_ZERO,
)

# Property [Decimal128 Boundary Behavior]: $sum preserves Decimal128 precision
# at extreme values and handles overflow/underflow correctly.
SUM_DECIMAL128_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "d128bound_max_identity",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_MAX, "b": DECIMAL128_ZERO},
        expected=DECIMAL128_MAX,
        msg="$sum should preserve DECIMAL128_MAX when adding zero",
    ),
    ExpressionTestCase(
        "d128bound_min_identity",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_MIN, "b": DECIMAL128_ZERO},
        expected=DECIMAL128_MIN,
        msg="$sum should preserve DECIMAL128_MIN when adding zero",
    ),
    ExpressionTestCase(
        "d128bound_max_roundtrip",
        expression={"$sum": ["$a", "$b", "$c"]},
        doc={"a": DECIMAL128_MAX, "b": Decimal128("-1E+6144"), "c": DECIMAL128_LARGE_EXPONENT},
        expected=DECIMAL128_MAX,
        msg="$sum should return DECIMAL128_MAX after subtracting and re-adding 1E+6144",
    ),
    ExpressionTestCase(
        "d128bound_min_roundtrip",
        expression={"$sum": ["$a", "$b", "$c"]},
        doc={"a": DECIMAL128_MIN, "b": DECIMAL128_LARGE_EXPONENT, "c": Decimal128("-1E+6144")},
        expected=DECIMAL128_MIN,
        msg="$sum should return DECIMAL128_MIN after adding and re-subtracting 1E+6144",
    ),
    ExpressionTestCase(
        "d128bound_min_positive_sum",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_MIN_POSITIVE, "b": DECIMAL128_MIN_POSITIVE},
        expected=Decimal128("2E-6176"),
        msg="$sum should correctly add two smallest positive Decimal128 values",
    ),
    ExpressionTestCase(
        "d128bound_max_negative_sum",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_MAX_NEGATIVE, "b": DECIMAL128_MAX_NEGATIVE},
        expected=Decimal128("-2E-6176"),
        msg="$sum should correctly add two most negative Decimal128 subnormals",
    ),
    ExpressionTestCase(
        "d128bound_cancel_at_min_positive",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_MIN_POSITIVE, "b": DECIMAL128_MAX_NEGATIVE},
        expected=Decimal128("0E-6176"),
        msg="$sum should cancel min positive and max negative Decimal128 to zero with exponent",
    ),
]

# Property [Decimal128 Precision]: Decimal128 arithmetic preserves full 34-digit precision.
SUM_DECIMAL128_PRECISION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "d128_exact_addition",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": Decimal128("0.1"), "b": Decimal128("0.2")},
        expected=Decimal128("0.3"),
        msg="$sum should compute exact 0.1+0.2=0.3 with Decimal128",
    ),
    ExpressionTestCase(
        "d128_trailing_zeros",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": Decimal128("1.00"), "b": Decimal128("2.00")},
        expected=Decimal128("3.00"),
        msg="$sum should preserve trailing zeros in Decimal128",
    ),
    ExpressionTestCase(
        "d128_34_digit",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": Decimal128("1234567890123456789012345678901234"), "b": DECIMAL128_ZERO},
        expected=Decimal128("1234567890123456789012345678901234"),
        msg="$sum should preserve full 34-digit Decimal128 precision",
    ),
    ExpressionTestCase(
        "d128_small_exponent",
        expression={"$sum": "$a"},
        doc={"a": DECIMAL128_MIN_POSITIVE},
        expected=DECIMAL128_MIN_POSITIVE,
        msg="$sum should preserve Decimal128 with smallest exponent",
    ),
    ExpressionTestCase(
        "d128_large_exponent",
        expression={"$sum": "$a"},
        doc={"a": DECIMAL128_LARGE_EXPONENT},
        expected=Decimal128("1.000000000000000000000000000000000E+6144"),
        msg="$sum should preserve Decimal128 with largest exponent",
    ),
    ExpressionTestCase(
        "d128_max",
        expression={"$sum": "$a"},
        doc={"a": DECIMAL128_MAX},
        expected=DECIMAL128_MAX,
        msg="$sum should preserve max representable Decimal128",
    ),
    ExpressionTestCase(
        "d128_min",
        expression={"$sum": "$a"},
        doc={"a": DECIMAL128_MIN},
        expected=DECIMAL128_MIN,
        msg="$sum should preserve min representable Decimal128",
    ),
    ExpressionTestCase(
        "d128_34_digit_rounding",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_MAX_COEFFICIENT, "b": Decimal128("1")},
        expected=Decimal128("1.000000000000000000000000000000000E+34"),
        msg="$sum should round when Decimal128 result exceeds 34 digits",
    ),
    ExpressionTestCase(
        "d128_min_positive_negation",
        expression={"$sum": "$a"},
        doc={"a": DECIMAL128_MAX_NEGATIVE},
        expected=DECIMAL128_MAX_NEGATIVE,
        msg="$sum should preserve negation of min positive Decimal128",
    ),
    ExpressionTestCase(
        "d128_different_scales_preserved",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": Decimal128("1E+33"), "b": Decimal128("1")},
        expected=Decimal128("1000000000000000000000000000000001"),
        msg="$sum should preserve both values when scale difference fits in 34 digits",
    ),
    ExpressionTestCase(
        "d128_different_scales_lost",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": Decimal128("1E+34"), "b": Decimal128("1")},
        expected=Decimal128("1.000000000000000000000000000000000E+34"),
        msg="$sum should lose small value when scale difference exceeds 34 digits",
    ),
]

# Property [Banker's Rounding]: When a Decimal128 result exceeds 34 significant
# digits, the halfway tie-breaking uses round-half-to-even (Banker's rounding).
# Each sum below produces a 35-digit exact result. The 35th digit is the
# rounding digit. When it is exactly 5 (halfway), the 34th digit determines
# the direction: even keeps its value, odd rounds away from zero.
SUM_DECIMAL128_BANKERS_ROUNDING_TESTS: list[ExpressionTestCase] = [
    # exact result: 1000000000000000000000000000000000|5 (34th digit 0, even → round down)
    ExpressionTestCase(
        "d128_bankers_half_even_down",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_MAX_COEFFICIENT, "b": Decimal128("6")},
        expected=Decimal128("1.000000000000000000000000000000000E+34"),
        msg="$sum should round half to even (down) when 34th digit is 0 (even)",
    ),
    # exact result: 1000000000000000000000000000000001|5 (34th digit 1, odd → round up)
    ExpressionTestCase(
        "d128_bankers_half_even_up",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_MAX_COEFFICIENT, "b": Decimal128("16")},
        expected=Decimal128("1.000000000000000000000000000000002E+34"),
        msg="$sum should round half to even (up) when 34th digit is 1 (odd)",
    ),
    # exact result: -1000000000000000000000000000000000|5 (34th digit 0, even → toward zero)
    ExpressionTestCase(
        "d128_bankers_half_even_negative_down",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_MIN_COEFFICIENT, "b": Decimal128("-6")},
        expected=Decimal128("-1.000000000000000000000000000000000E+34"),
        msg="$sum should round negative half to even (toward zero) when 34th digit is 0",
    ),
    # exact result: -1000000000000000000000000000000001|5 (34th digit 1, odd → away from zero)
    ExpressionTestCase(
        "d128_bankers_half_even_negative_up",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_MIN_COEFFICIENT, "b": Decimal128("-16")},
        expected=Decimal128("-1.000000000000000000000000000000002E+34"),
        msg="$sum should round negative half to even (away from zero) when 34th digit is 1",
    ),
]

# Property [Cross-Type Precision]: mixing double with Decimal128 reveals the full conversion.
SUM_MIXED_PRECISION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "mixed_inexact_double",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": 3.14, "b": DECIMAL128_ZERO},
        expected=Decimal128("3.140000000000000124344978758017533"),
        msg="$sum should expose double imprecision when mixed with Decimal128",
    ),
    ExpressionTestCase(
        "mixed_exact_double",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": 1.0, "b": DECIMAL128_ZERO},
        expected=Decimal128("1"),
        msg="$sum should produce clean Decimal128 for exact double mixed with Decimal128",
    ),
]

# Property [Decimal128 Overflow]: Decimal128 overflow produces the corresponding Infinity value.
SUM_DECIMAL128_OVERFLOW_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "overflow_decimal128_positive",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_MAX, "b": DECIMAL128_LARGE_EXPONENT},
        expected=DECIMAL128_INFINITY,
        msg="$sum should return Decimal128 Infinity when Decimal128 overflows positively",
    ),
    ExpressionTestCase(
        "overflow_decimal128_negative",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_MIN, "b": Decimal128("-1E+6144")},
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="$sum should return Decimal128 -Infinity when Decimal128 overflows negatively",
    ),
]

SUM_DECIMAL128_ALL_TESTS = (
    SUM_DECIMAL128_BOUNDARY_TESTS
    + SUM_DECIMAL128_PRECISION_TESTS
    + SUM_DECIMAL128_BANKERS_ROUNDING_TESTS
    + SUM_MIXED_PRECISION_TESTS
    + SUM_DECIMAL128_OVERFLOW_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SUM_DECIMAL128_ALL_TESTS))
def test_sum_decimal128(collection, test_case: ExpressionTestCase):
    """Test $sum Decimal128 boundary, precision, and overflow."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
