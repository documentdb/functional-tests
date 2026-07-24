"""$toLong arity and field path syntax tests."""

import pytest
from bson import Int64

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

# Property [Arity]: $toLong unwraps single-element literal arrays and rejects empty or
# multi-element arrays. These cases are specific to $toLong syntax (not $convert).
TOLONG_ARITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "single_element",
        msg="Single-element literal array argument is unwrapped to a scalar",
        expression={"$toLong": [42]},
        expected=Int64(42),
    ),
    ExpressionTestCase(
        "empty_array",
        msg="Empty literal array argument is an arity error",
        expression={"$toLong": []},
        error_code=TO_TYPE_ARITY_ERROR,
    ),
    ExpressionTestCase(
        "multi_element",
        msg="Multi-element literal array argument is an arity error",
        expression={"$toLong": [1, 2]},
        error_code=TO_TYPE_ARITY_ERROR,
    ),
    ExpressionTestCase(
        "single_null",
        msg="Single-element literal array wrapping null unwraps and returns null",
        expression={"$toLong": [None]},
        expected=None,
    ),
    ExpressionTestCase(
        "large_array",
        msg="A large literal array argument is an arity error",
        expression={"$toLong": list(range(100))},
        error_code=TO_TYPE_ARITY_ERROR,
    ),
]

# Property [Invalid Field Path]: $toLong rejects malformed field path syntax.
TOLONG_INVALID_FIELD_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "bare_dollar",
        msg="Bare '$' is an invalid field path",
        expression={"$toLong": "$"},
        error_code=INVALID_DOLLAR_FIELD_PATH,
    ),
    ExpressionTestCase(
        "double_dollar",
        msg="'$$' is rejected as an empty variable name",
        expression={"$toLong": "$$"},
        error_code=FAILED_TO_PARSE_ERROR,
    ),
]


@pytest.mark.parametrize(
    "test", pytest_params(TOLONG_ARITY_TESTS + TOLONG_INVALID_FIELD_PATH_TESTS)
)
def test_toLong_arity(collection, test: ExpressionTestCase):
    """$toLong literal array arguments are unwrapped or rejected based on arity."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
