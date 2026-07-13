"""$toDecimal arity and field path syntax tests."""

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import (
    FAILED_TO_PARSE_ERROR,
    INVALID_DOLLAR_FIELD_PATH,
    TO_TYPE_ARITY_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Arity]: $toDecimal unwraps a single-element literal array at parse time;
# empty and multi-element arrays are arity errors.
TODECIMAL_ARITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "single_element",
        msg="Single-element literal array argument is unwrapped to a scalar",
        expression={"$toDecimal": [42]},
        expected=Decimal128("42"),
    ),
    ExpressionTestCase(
        "single_null",
        msg="Single-element literal array wrapping null unwraps and returns null",
        expression={"$toDecimal": [None]},
        expected=None,
    ),
    ExpressionTestCase(
        "empty_array",
        msg="Empty literal array argument is an arity error",
        expression={"$toDecimal": []},
        error_code=TO_TYPE_ARITY_ERROR,
    ),
    ExpressionTestCase(
        "multi_element",
        msg="Multi-element literal array argument is an arity error",
        expression={"$toDecimal": [1, 2]},
        error_code=TO_TYPE_ARITY_ERROR,
    ),
    ExpressionTestCase(
        "large_array",
        msg="Large literal array argument is an arity error",
        expression={"$toDecimal": list(range(100))},
        error_code=TO_TYPE_ARITY_ERROR,
    ),
]

# Property [Invalid Field Path]: $toDecimal rejects malformed field path syntax.
TODECIMAL_INVALID_FIELD_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "bare_dollar",
        msg="Bare '$' is an invalid field path",
        expression={"$toDecimal": "$"},
        error_code=INVALID_DOLLAR_FIELD_PATH,
    ),
    ExpressionTestCase(
        "double_dollar",
        msg="'$$' is rejected as an empty variable name",
        expression={"$toDecimal": "$$"},
        error_code=FAILED_TO_PARSE_ERROR,
    ),
]


@pytest.mark.parametrize("test", pytest_params(TODECIMAL_ARITY_TESTS))
def test_toDecimal_arity(collection, test: ExpressionTestCase):
    """$toDecimal literal array arguments are unwrapped or rejected based on arity."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(TODECIMAL_INVALID_FIELD_PATH_TESTS))
def test_toDecimal_invalid_field_path(collection, test: ExpressionTestCase):
    """$toDecimal rejects invalid field path syntax."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
