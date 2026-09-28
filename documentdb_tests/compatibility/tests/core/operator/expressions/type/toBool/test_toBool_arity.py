"""$toBool arity and field path syntax tests."""

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
from documentdb_tests.framework.test_constants import INT32_ZERO

# Property [Arity]: $toBool unwraps single-element literal arrays and rejects empty or
# multi-element arrays. These cases are specific to $toBool syntax (not $convert).
TOBOOL_ARITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "single_element",
        msg="Single-element literal array wrapping a falsy value unwraps and converts to false",
        expression={"$toBool": [False]},
        expected=False,
    ),
    ExpressionTestCase(
        "single_null",
        msg="Single-element literal array wrapping null unwraps and returns null",
        expression={"$toBool": [None]},
        expected=None,
    ),
    ExpressionTestCase(
        "single_nested_array",
        msg="Single-element array wrapping an inner array unwraps; the inner array is truthy",
        expression={"$toBool": [[INT32_ZERO]]},
        expected=True,
    ),
    ExpressionTestCase(
        "empty_array",
        msg="Empty literal array argument is an arity error",
        expression={"$toBool": []},
        error_code=TO_TYPE_ARITY_ERROR,
    ),
    ExpressionTestCase(
        "two_elements",
        msg="Two-element literal array argument is an arity error",
        expression={"$toBool": [1, 2]},
        error_code=TO_TYPE_ARITY_ERROR,
    ),
    ExpressionTestCase(
        "large_array",
        msg="Large literal array argument is an arity error",
        expression={"$toBool": list(range(100))},
        error_code=TO_TYPE_ARITY_ERROR,
    ),
]

# Property [Invalid Field Path]: $toBool rejects malformed field path syntax.
TOBOOL_INVALID_FIELD_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "bare_dollar",
        msg="Bare '$' is an invalid field path",
        expression={"$toBool": "$"},
        error_code=INVALID_DOLLAR_FIELD_PATH,
    ),
    ExpressionTestCase(
        "double_dollar",
        msg="'$$' is rejected as an empty variable name",
        expression={"$toBool": "$$"},
        error_code=FAILED_TO_PARSE_ERROR,
    ),
]


@pytest.mark.parametrize(
    "test", pytest_params(TOBOOL_ARITY_TESTS + TOBOOL_INVALID_FIELD_PATH_TESTS)
)
def test_toBool_arity(collection, test: ExpressionTestCase):
    """$toBool literal array arguments are unwrapped or rejected based on arity."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
