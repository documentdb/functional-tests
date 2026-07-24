"""
Error and argument handling tests for $isArray expression.

Tests arity errors.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import EXPRESSION_TYPE_MISMATCH_ERROR
from documentdb_tests.framework.parametrize import pytest_params

# Property [Arity]: $isArray requires exactly one argument.
ARITY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "zero_args",
        expression={"$isArray": []},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$isArray should reject zero arguments",
    ),
    ExpressionTestCase(
        "two_args",
        expression={"$isArray": [1, 2]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$isArray should reject two arguments",
    ),
    ExpressionTestCase(
        "three_args",
        expression={"$isArray": [1, 2, 3]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$isArray should reject three arguments",
    ),
]

ALL_ERROR_TESTS = ARITY_ERROR_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_ERROR_TESTS))
def test_isArray_error(collection, test):
    """Test $isArray error cases."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
