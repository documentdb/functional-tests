"""$toInt arity and field path syntax tests."""

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

# Property [Arity]: $toInt unwraps single-element literal arrays and rejects empty or
# multi-element arrays. These cases are specific to $toInt syntax (not $convert).
TOINT_ARITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "single_element",
        msg="Single-element literal array argument is unwrapped to a scalar",
        expression={"$toInt": [42]},
        expected=42,
    ),
    ExpressionTestCase(
        "empty_array",
        msg="Empty literal array argument is an arity error",
        expression={"$toInt": []},
        error_code=TO_TYPE_ARITY_ERROR,
    ),
    ExpressionTestCase(
        "multi_element",
        msg="Multi-element literal array argument is an arity error",
        expression={"$toInt": [1, 2]},
        error_code=TO_TYPE_ARITY_ERROR,
    ),
    ExpressionTestCase(
        "single_null",
        msg="Single-element literal array wrapping null unwraps and returns null",
        expression={"$toInt": [None]},
        expected=None,
    ),
    ExpressionTestCase(
        "single_bool",
        msg="Single-element literal array wrapping a bool unwraps and converts",
        expression={"$toInt": [True]},
        expected=1,
    ),
    ExpressionTestCase(
        "large_array",
        msg="A large literal array argument is an arity error",
        expression={"$toInt": list(range(100))},
        error_code=TO_TYPE_ARITY_ERROR,
    ),
]

# Property [Invalid Field Path]: $toInt rejects malformed field path syntax.
TOINT_INVALID_FIELD_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "bare_dollar",
        msg="Bare '$' is an invalid field path",
        expression={"$toInt": "$"},
        error_code=INVALID_DOLLAR_FIELD_PATH,
    ),
    ExpressionTestCase(
        "double_dollar",
        msg="'$$' is rejected as an empty variable name",
        expression={"$toInt": "$$"},
        error_code=FAILED_TO_PARSE_ERROR,
    ),
]


@pytest.mark.parametrize("test", pytest_params(TOINT_ARITY_TESTS + TOINT_INVALID_FIELD_PATH_TESTS))
def test_toInt_arity(collection, test: ExpressionTestCase):
    """$toInt literal array arguments are unwrapped or rejected based on arity."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
