"""Non-finite (NaN/Infinity) tests for the $subtract operator."""

from __future__ import annotations

import math

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
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [Infinity]: $subtract propagates infinity values.
SUBTRACT_INFINITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "infinity",
        doc={},
        expression={"$subtract": [FLOAT_INFINITY, 1]},
        expected=FLOAT_INFINITY,
        msg="Should subtract from positive infinity",
    ),
    ExpressionTestCase(
        "negative_infinity",
        doc={},
        expression={"$subtract": [FLOAT_NEGATIVE_INFINITY, 1]},
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="Should subtract from negative infinity",
    ),
    ExpressionTestCase(
        "subtract_infinity",
        doc={},
        expression={"$subtract": [1, FLOAT_INFINITY]},
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="Should subtract positive infinity",
    ),
    ExpressionTestCase(
        "subtract_neg_infinity",
        doc={},
        expression={"$subtract": [1, FLOAT_NEGATIVE_INFINITY]},
        expected=FLOAT_INFINITY,
        msg="Should subtract negative infinity",
    ),
    ExpressionTestCase(
        "inf_minus_zero",
        doc={},
        expression={"$subtract": [FLOAT_INFINITY, 0]},
        expected=FLOAT_INFINITY,
        msg="Should subtract zero from positive infinity",
    ),
    ExpressionTestCase(
        "neg_inf_minus_zero",
        doc={},
        expression={"$subtract": [FLOAT_NEGATIVE_INFINITY, 0]},
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="Should subtract zero from negative infinity",
    ),
    ExpressionTestCase(
        "inf_minus_inf",
        doc={},
        expression={"$subtract": [FLOAT_INFINITY, FLOAT_INFINITY]},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN for infinity minus infinity",
    ),
    ExpressionTestCase(
        "neg_inf_minus_neg_inf",
        doc={},
        expression={"$subtract": [FLOAT_NEGATIVE_INFINITY, FLOAT_NEGATIVE_INFINITY]},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN for negative infinity minus negative infinity",
    ),
    ExpressionTestCase(
        "decimal_infinity",
        doc={},
        expression={"$subtract": [DECIMAL128_INFINITY, 1]},
        expected=DECIMAL128_INFINITY,
        msg="Should subtract from decimal infinity",
    ),
    ExpressionTestCase(
        "decimal_negative_infinity",
        doc={},
        expression={"$subtract": [DECIMAL128_NEGATIVE_INFINITY, 1]},
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="Should subtract from decimal negative infinity",
    ),
    ExpressionTestCase(
        "decimal_inf_minus_inf",
        doc={},
        expression={"$subtract": [DECIMAL128_INFINITY, DECIMAL128_INFINITY]},
        expected=DECIMAL128_NAN,
        msg="Should return decimal NaN for decimal infinity minus decimal infinity",
    ),
    ExpressionTestCase(
        "decimal_inf_minus_int",
        doc={},
        expression={"$subtract": [DECIMAL128_INFINITY, 1]},
        expected=DECIMAL128_INFINITY,
        msg="Should subtract int from decimal infinity",
    ),
    ExpressionTestCase(
        "int_minus_decimal_inf",
        doc={},
        expression={"$subtract": [1, DECIMAL128_INFINITY]},
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="Should subtract decimal infinity from int",
    ),
]

# Property [NaN]: $subtract propagates NaN values.
SUBTRACT_NAN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nan_minuend",
        doc={},
        expression={"$subtract": [FLOAT_NAN, 1]},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN when minuend is NaN",
    ),
    ExpressionTestCase(
        "nan_subtrahend",
        doc={},
        expression={"$subtract": [10, FLOAT_NAN]},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN when subtrahend is NaN",
    ),
    ExpressionTestCase(
        "both_nan",
        doc={},
        expression={"$subtract": [FLOAT_NAN, FLOAT_NAN]},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN when both operands are NaN",
    ),
    ExpressionTestCase(
        "decimal_nan_minuend",
        doc={},
        expression={"$subtract": [DECIMAL128_NAN, 1]},
        expected=DECIMAL128_NAN,
        msg="Should return decimal NaN when minuend is decimal NaN",
    ),
    ExpressionTestCase(
        "decimal_nan_subtrahend",
        doc={},
        expression={"$subtract": [10, DECIMAL128_NAN]},
        expected=DECIMAL128_NAN,
        msg="Should return decimal NaN when subtrahend is decimal NaN",
    ),
    ExpressionTestCase(
        "decimal_nan_minus_double",
        doc={},
        expression={"$subtract": [DECIMAL128_NAN, 1.5]},
        expected=DECIMAL128_NAN,
        msg="Should return decimal NaN for decimal NaN minus double",
    ),
    ExpressionTestCase(
        "double_minus_decimal_nan",
        doc={},
        expression={"$subtract": [1.5, DECIMAL128_NAN]},
        expected=DECIMAL128_NAN,
        msg="Should return decimal NaN for double minus decimal NaN",
    ),
]

SUBTRACT_NON_FINITE_TESTS = SUBTRACT_INFINITY_TESTS + SUBTRACT_NAN_TESTS


@pytest.mark.parametrize("test_case", pytest_params(SUBTRACT_NON_FINITE_TESTS))
def test_subtract_non_finite(collection, test_case: ExpressionTestCase):
    """Test $subtract non-finite value cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
