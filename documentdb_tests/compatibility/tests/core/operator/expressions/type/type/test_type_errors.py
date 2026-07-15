"""$type error handling tests.

Tests that $type rejects invalid arity, malformed field path syntax, and
propagates errors from inner expressions.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    EXPRESSION_TYPE_MISMATCH_ERROR,
    FAILED_TO_PARSE_ERROR,
    INVALID_DOLLAR_FIELD_PATH,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import INT32_ZERO

# Property [Arity Errors]: $type takes exactly one argument; zero or multiple
# arguments produce an error.
TYPE_ARITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "arity_zero_args",
        expression={"$type": []},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$type should reject zero arguments",
    ),
    ExpressionTestCase(
        "arity_two_args",
        expression={"$type": ["a", "b"]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$type should reject two arguments",
    ),
]

# Property [Syntax Validation]: bare "$" and "$$" as the expression produce
# field path and variable name errors respectively.
TYPE_SYNTAX_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "syntax_bare_dollar",
        expression={"$type": "$"},
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$type should reject bare '$' as an invalid field path",
    ),
    ExpressionTestCase(
        "syntax_bare_double_dollar",
        expression={"$type": "$$"},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$type should reject bare '$$' as an empty variable name",
    ),
]

# Property [Error Propagation]: when the inner expression produces an error,
# that error propagates through $type rather than returning a type name.
TYPE_ERROR_PROPAGATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "error_prop_divide_by_zero",
        expression={"$type": {"$divide": [1, INT32_ZERO]}},
        error_code=BAD_VALUE_ERROR,
        msg="$type should propagate the inner expression's division-by-zero error",
    ),
]

TYPE_ERROR_TESTS = TYPE_ARITY_TESTS + TYPE_SYNTAX_TESTS + TYPE_ERROR_PROPAGATION_TESTS


@pytest.mark.parametrize("test", pytest_params(TYPE_ERROR_TESTS))
def test_type_errors(collection, test: ExpressionTestCase):
    """$type rejects invalid arguments and propagates inner expression errors."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
