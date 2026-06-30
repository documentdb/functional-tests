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

# Property [Infinity]: $abs of positive or negative infinity returns positive infinity.
ABS_INFINITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "float_infinity",
        doc={"value": FLOAT_INFINITY},
        expression={"$abs": ["$value"]},
        expected=FLOAT_INFINITY,
        msg="$abs should return float infinity for float infinity",
    ),
    ExpressionTestCase(
        "float_negative_infinity",
        doc={"value": FLOAT_NEGATIVE_INFINITY},
        expression={"$abs": ["$value"]},
        expected=FLOAT_INFINITY,
        msg="$abs should return positive infinity for float negative infinity",
    ),
    ExpressionTestCase(
        "decimal128_infinity",
        doc={"value": DECIMAL128_INFINITY},
        expression={"$abs": ["$value"]},
        expected=DECIMAL128_INFINITY,
        msg="$abs should return decimal128 infinity for decimal128 infinity",
    ),
    ExpressionTestCase(
        "decimal128_negative_infinity",
        doc={"value": DECIMAL128_NEGATIVE_INFINITY},
        expression={"$abs": ["$value"]},
        expected=DECIMAL128_INFINITY,
        msg="$abs should return decimal128 positive infinity for decimal128 negative infinity",
    ),
]

# Property [NaN]: $abs of NaN returns NaN of the same type.
ABS_NAN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "float_nan",
        doc={"value": FLOAT_NAN},
        expression={"$abs": ["$value"]},
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$abs should return NaN for float NaN",
    ),
    ExpressionTestCase(
        "decimal128_nan",
        doc={"value": DECIMAL128_NAN},
        expression={"$abs": ["$value"]},
        expected=DECIMAL128_NAN,
        msg="$abs should return NaN for decimal128 NaN",
    ),
]

ABS_NON_FINITE_TESTS = ABS_INFINITY_TESTS + ABS_NAN_TESTS


@pytest.mark.parametrize("test_case", pytest_params(ABS_NON_FINITE_TESTS))
def test_abs_non_finite(collection, test_case: ExpressionTestCase):
    """Test $abs infinity and NaN cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
