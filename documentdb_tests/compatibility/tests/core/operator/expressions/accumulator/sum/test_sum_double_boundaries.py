from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DOUBLE_MAX,
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_MIN,
    DOUBLE_MIN_NORMAL,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [Double Boundary Behavior]: $sum handles double precision limits,
# subnormals, and near-max values correctly.
SUM_DOUBLE_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "float_pos_zero",
        expression={"$sum": "$a"},
        doc={"a": DOUBLE_ZERO},
        expected=DOUBLE_ZERO,
        msg="$sum should preserve positive zero double",
    ),
    ExpressionTestCase(
        "float_subnormal",
        expression={"$sum": "$a"},
        doc={"a": DOUBLE_MIN_SUBNORMAL},
        expected=DOUBLE_MIN_SUBNORMAL,
        msg="$sum should preserve subnormal double",
    ),
    ExpressionTestCase(
        "float_subnormal_sum",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DOUBLE_MIN_SUBNORMAL, "b": DOUBLE_MIN_SUBNORMAL},
        expected=1e-323,
        msg="$sum should correctly add two subnormal doubles",
    ),
    ExpressionTestCase(
        "float_min_normal",
        expression={"$sum": "$a"},
        doc={"a": DOUBLE_MIN_NORMAL},
        expected=DOUBLE_MIN_NORMAL,
        msg="$sum should preserve DBL_MIN (smallest normal double)",
    ),
    ExpressionTestCase(
        "float_min_normal_sum",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DOUBLE_MIN_NORMAL / 2.0, "b": DOUBLE_MIN_NORMAL / 2.0},
        expected=DOUBLE_MIN_NORMAL,
        msg="$sum should produce DBL_MIN from two subnormal halves",
    ),
    ExpressionTestCase(
        "float_max",
        expression={"$sum": "$a"},
        doc={"a": DOUBLE_MAX},
        expected=DOUBLE_MAX,
        msg="$sum should preserve DBL_MAX",
    ),
    ExpressionTestCase(
        "float_max_sum",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DOUBLE_MAX / 2.0, "b": DOUBLE_MAX / 2.0},
        expected=DOUBLE_MAX,
        msg="$sum should produce DBL_MAX from two halves",
    ),
    ExpressionTestCase(
        "float_min",
        expression={"$sum": "$a"},
        doc={"a": DOUBLE_MIN},
        expected=DOUBLE_MIN,
        msg="$sum should preserve most negative double",
    ),
    ExpressionTestCase(
        "float_min_sum",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DOUBLE_MIN / 2.0, "b": DOUBLE_MIN / 2.0},
        expected=DOUBLE_MIN,
        msg="$sum should produce most negative double from two halves",
    ),
    ExpressionTestCase(
        "float_max_safe_integer",
        expression={"$sum": "$a"},
        doc={"a": float(DOUBLE_MAX_SAFE_INTEGER)},
        expected=float(DOUBLE_MAX_SAFE_INTEGER),
        msg="$sum should preserve max safe integer double",
    ),
    ExpressionTestCase(
        "float_max_safe_integer_sum",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": float(DOUBLE_MAX_SAFE_INTEGER) - 1.0, "b": 1.0},
        expected=float(DOUBLE_MAX_SAFE_INTEGER),
        msg="$sum should produce max safe integer from (MSI-1) + 1.0",
    ),
    ExpressionTestCase(
        "float_precision_loss_plus_one_absorbed",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": float(DOUBLE_MAX_SAFE_INTEGER), "b": 1.0},
        expected=float(DOUBLE_MAX_SAFE_INTEGER),
        msg="$sum should absorb adding 1.0 to max safe integer double due to precision loss",
    ),
]

# Property [Double Precision]: $sum produces accurate results for
# double operands beyond what naive floating-point addition yields.
SUM_COMPENSATED_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "compensated_point_one_two_three",
        expression={"$sum": ["$a", "$b", "$c"]},
        doc={"a": 0.1, "b": 0.2, "c": 0.3},
        expected=0.6,
        msg="$sum should return exact 0.6 for 0.1+0.2+0.3 via compensated summation",
    ),
    ExpressionTestCase(
        "compensated_repeated_tenth",
        expression={"$sum": "$a"},
        doc={"a": [0.1] * 10},
        expected=1.0,
        msg="$sum should return exact 1.0 for ten 0.1 values via compensated summation",
    ),
    ExpressionTestCase(
        "compensated_large_plus_small",
        expression={"$sum": ["$a", "$b", "$c"]},
        doc={"a": 1e15, "b": 1.0, "c": -1e15},
        expected=1.0,
        msg="$sum should preserve small addend via compensated summation",
    ),
]

# Property [Double Overflow]: double overflow produces the corresponding Infinity value.
SUM_DOUBLE_OVERFLOW_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "overflow_double_positive",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DOUBLE_MAX, "b": DOUBLE_MAX},
        expected=FLOAT_INFINITY,
        msg="$sum should return Infinity when double overflows positively",
    ),
    ExpressionTestCase(
        "overflow_double_negative",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DOUBLE_MIN, "b": DOUBLE_MIN},
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$sum should return -Infinity when double overflows negatively",
    ),
]

SUM_DOUBLE_ALL_TESTS = SUM_DOUBLE_BOUNDARY_TESTS + SUM_COMPENSATED_TESTS + SUM_DOUBLE_OVERFLOW_TESTS


@pytest.mark.parametrize("test_case", pytest_params(SUM_DOUBLE_ALL_TESTS))
def test_sum_double_boundaries(collection, test_case: ExpressionTestCase):
    """Test $sum double boundary, precision, and overflow."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
