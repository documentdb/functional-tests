"""
Error and argument handling tests for $isArray expression.

Tests arity errors.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import EXPRESSION_TYPE_MISMATCH_ERROR

# Arity errors
ARITY_ERROR_TESTS = [
    pytest.param({"$isArray": []}, id="zero_args"),
    pytest.param({"$isArray": [1, 2]}, id="two_args"),
    pytest.param({"$isArray": [1, 2, 3]}, id="three_args"),
]


@pytest.mark.parametrize("expr", ARITY_ERROR_TESTS)
def test_isArray_arity_error(collection, expr):
    """Test $isArray errors with wrong number of arguments."""
    result = execute_expression(collection, expr)
    assert_expression_result(result, error_code=EXPRESSION_TYPE_MISMATCH_ERROR)
