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
    DOUBLE_ONE_AND_HALF,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_ZERO,
)

pytestmark = pytest.mark.aggregate

# Property [Infinity propagation]: $subtract propagates Infinity when one operand is infinite.
INFINITY_PROPAGATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "infinity_minuend",
        doc={"a": FLOAT_INFINITY, "b": 1},
        expression={"$subtract": ["$a", "$b"]},
        expected=FLOAT_INFINITY,
        msg="$subtract of Infinity minus a number should return Infinity",
    ),
    ExpressionTestCase(
        "negative_infinity_minuend",
        doc={"a": FLOAT_NEGATIVE_INFINITY, "b": 1},
        expression={"$subtract": ["$a", "$b"]},
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$subtract of -Infinity minus a number should return -Infinity",
    ),
    ExpressionTestCase(
        "infinity_subtrahend",
        doc={"a": 1, "b": FLOAT_INFINITY},
        expression={"$subtract": ["$a", "$b"]},
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$subtract of a number minus Infinity should return -Infinity",
    ),
    ExpressionTestCase(
        "negative_infinity_subtrahend",
        doc={"a": 1, "b": FLOAT_NEGATIVE_INFINITY},
        expression={"$subtract": ["$a", "$b"]},
        expected=FLOAT_INFINITY,
        msg="$subtract of a number minus -Infinity should return Infinity",
    ),
    ExpressionTestCase(
        "inf_minus_zero",
        doc={"a": FLOAT_INFINITY, "b": INT32_ZERO},
        expression={"$subtract": ["$a", "$b"]},
        expected=FLOAT_INFINITY,
        msg="$subtract of Infinity minus zero should return Infinity",
    ),
    ExpressionTestCase(
        "neg_inf_minus_zero",
        doc={"a": FLOAT_NEGATIVE_INFINITY, "b": INT32_ZERO},
        expression={"$subtract": ["$a", "$b"]},
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$subtract of -Infinity minus zero should return -Infinity",
    ),
    ExpressionTestCase(
        "inf_minus_inf",
        doc={"a": FLOAT_INFINITY, "b": FLOAT_INFINITY},
        expression={"$subtract": ["$a", "$b"]},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="$subtract of Infinity minus Infinity should return NaN",
    ),
    ExpressionTestCase(
        "neg_inf_minus_neg_inf",
        doc={"a": FLOAT_NEGATIVE_INFINITY, "b": FLOAT_NEGATIVE_INFINITY},
        expression={"$subtract": ["$a", "$b"]},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="$subtract of -Infinity minus -Infinity should return NaN",
    ),
    # Decimal128 Infinity
    ExpressionTestCase(
        "decimal_infinity_minuend",
        doc={"a": DECIMAL128_INFINITY, "b": 1},
        expression={"$subtract": ["$a", "$b"]},
        expected=DECIMAL128_INFINITY,
        msg="$subtract of Decimal128 Infinity minus a number should return Decimal128 Infinity",
    ),
    ExpressionTestCase(
        "decimal_negative_infinity_minuend",
        doc={"a": DECIMAL128_NEGATIVE_INFINITY, "b": 1},
        expression={"$subtract": ["$a", "$b"]},
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="$subtract of Decimal128 -Infinity minus a number should return Decimal128 -Infinity",
    ),
    ExpressionTestCase(
        "decimal_inf_minus_inf",
        doc={"a": DECIMAL128_INFINITY, "b": DECIMAL128_INFINITY},
        expression={"$subtract": ["$a", "$b"]},
        expected=DECIMAL128_NAN,
        msg="$subtract of Decimal128 Infinity minus Decimal128 Infinity should return Decimal128 NaN",  # noqa: E501
    ),
]

# Property [NaN propagation]: $subtract propagates NaN when either operand is NaN.
NAN_PROPAGATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nan_minuend",
        doc={"a": FLOAT_NAN, "b": 1},
        expression={"$subtract": ["$a", "$b"]},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="$subtract with a NaN minuend should return NaN",
    ),
    ExpressionTestCase(
        "nan_subtrahend",
        doc={"a": 10, "b": FLOAT_NAN},
        expression={"$subtract": ["$a", "$b"]},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="$subtract with a NaN subtrahend should return NaN",
    ),
    ExpressionTestCase(
        "both_nan",
        doc={"a": FLOAT_NAN, "b": FLOAT_NAN},
        expression={"$subtract": ["$a", "$b"]},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="$subtract with both operands as NaN should return NaN",
    ),
    # Decimal128 NaN
    ExpressionTestCase(
        "decimal_nan_minuend",
        doc={"a": DECIMAL128_NAN, "b": 1},
        expression={"$subtract": ["$a", "$b"]},
        expected=DECIMAL128_NAN,
        msg="$subtract with a Decimal128 NaN minuend should return Decimal128 NaN",
    ),
    ExpressionTestCase(
        "decimal_nan_subtrahend",
        doc={"a": 10, "b": DECIMAL128_NAN},
        expression={"$subtract": ["$a", "$b"]},
        expected=DECIMAL128_NAN,
        msg="$subtract with a Decimal128 NaN subtrahend should return Decimal128 NaN",
    ),
]

# Property [Inf - Inf = NaN]: subtracting equal signed infinities produces NaN.
INF_MINUS_INF_NAN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "decimal_nan_minus_double",
        doc={"a": DECIMAL128_NAN, "b": DOUBLE_ONE_AND_HALF},
        expression={"$subtract": ["$a", "$b"]},
        expected=DECIMAL128_NAN,
        msg="$subtract of Decimal128 NaN minus a double should return Decimal128 NaN",
    ),
    ExpressionTestCase(
        "double_minus_decimal_nan",
        doc={"a": DOUBLE_ONE_AND_HALF, "b": DECIMAL128_NAN},
        expression={"$subtract": ["$a", "$b"]},
        expected=DECIMAL128_NAN,
        msg="$subtract of a double minus Decimal128 NaN should return Decimal128 NaN",
    ),
    ExpressionTestCase(
        "int_minus_decimal_inf",
        doc={"a": 1, "b": DECIMAL128_INFINITY},
        expression={"$subtract": ["$a", "$b"]},
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="$subtract of an int minus Decimal128 Infinity should return Decimal128 -Infinity",
    ),
]

SUBTRACT_NON_FINITE_TESTS: list[ExpressionTestCase] = (
    INFINITY_PROPAGATION_TESTS + NAN_PROPAGATION_TESTS + INF_MINUS_INF_NAN_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SUBTRACT_NON_FINITE_TESTS))
def test_subtract_non_finite(collection, test_case: ExpressionTestCase):
    """Test $subtract behavior with non-finite values (NaN and Infinity)."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
