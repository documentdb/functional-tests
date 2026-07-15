"""Tests for $log argument form, literal input, and nested expression input."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import EXPRESSION_TYPE_MISMATCH_ERROR
from documentdb_tests.framework.parametrize import pytest_params

# Property [Argument Form]: $log requires its two arguments in an array and rejects a bare
# non-array argument.
LOG_ARGUMENT_FORM_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "bare_non_array",
        doc={"value": 100},
        expression={"$log": "$value"},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$log should reject a bare non-array argument, requiring its value and base in an "
        "array",
    ),
]

# Property [Literal Input]: $log evaluates inline literal value and base arguments.
LOG_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal_input",
        doc={},
        expression={"$log": [100, 10]},
        expected=pytest.approx(2.0),
        msg="$log should return two for inline literal one hundred in base ten",
    ),
]

# Property [Expression Input]: $log evaluates a nested expression in the value or base argument
# before taking the logarithm.
LOG_EXPRESSION_INPUT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "expression_value",
        doc={},
        expression={"$log": [{"$add": [50, 50]}, 10]},
        expected=pytest.approx(2.0),
        msg="$log should evaluate a nested expression value argument",
    ),
    ExpressionTestCase(
        "expression_base",
        doc={},
        expression={"$log": [100, {"$add": [5, 5]}]},
        expected=pytest.approx(2.0),
        msg="$log should evaluate a nested expression base argument",
    ),
]

LOG_INPUT_FORM_TESTS = LOG_ARGUMENT_FORM_TESTS + LOG_LITERAL_TESTS + LOG_EXPRESSION_INPUT_TESTS


@pytest.mark.parametrize("test_case", pytest_params(LOG_INPUT_FORM_TESTS))
def test_log_input_forms(collection, test_case: ExpressionTestCase):
    """Test $log argument form, literal, and nested expression input cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
