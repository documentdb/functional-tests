"""$toDouble arity and field path syntax tests."""

import pytest

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

# Property [Arity]: $toDouble unwraps single-element literal arrays and rejects empty or
# multi-element arrays. These cases are specific to $toDouble syntax (not $convert).
TODOUBLE_ARITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "single_element",
        msg="Single-element literal array argument is unwrapped to a scalar",
        expression={"$toDouble": [42]},
        expected=42.0,
    ),
    ExpressionTestCase(
        "empty_array",
        msg="Empty literal array argument is an arity error",
        expression={"$toDouble": []},
        error_code=TO_TYPE_ARITY_ERROR,
    ),
    ExpressionTestCase(
        "multi_element",
        msg="Multi-element literal array argument is an arity error",
        expression={"$toDouble": [1, 2]},
        error_code=TO_TYPE_ARITY_ERROR,
    ),
    ExpressionTestCase(
        "single_null",
        msg="Single-element literal array wrapping null unwraps and returns null",
        expression={"$toDouble": [None]},
        expected=None,
    ),
    ExpressionTestCase(
        "single_bool",
        msg="Single-element literal array wrapping a bool unwraps and converts",
        expression={"$toDouble": [True]},
        expected=1.0,
    ),
    ExpressionTestCase(
        "large_array",
        msg="A large literal array argument is an arity error",
        expression={"$toDouble": list(range(100))},
        error_code=TO_TYPE_ARITY_ERROR,
    ),
]

# Property [Invalid Field Path]: $toDouble rejects malformed field path syntax.
TODOUBLE_INVALID_FIELD_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "bare_dollar",
        msg="Bare '$' is an invalid field path",
        expression={"$toDouble": "$"},
        error_code=INVALID_DOLLAR_FIELD_PATH,
    ),
    ExpressionTestCase(
        "double_dollar",
        msg="'$$' is rejected as an empty variable name",
        expression={"$toDouble": "$$"},
        error_code=FAILED_TO_PARSE_ERROR,
    ),
]


@pytest.mark.parametrize("test", pytest_params(TODOUBLE_ARITY_TESTS))
def test_toDouble_arity(collection, test: ExpressionTestCase):
    """$toDouble literal array arguments are unwrapped or rejected based on arity."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(TODOUBLE_INVALID_FIELD_PATH_TESTS))
def test_toDouble_invalid_field_path(collection, test: ExpressionTestCase):
    """$toDouble rejects invalid field path syntax."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
