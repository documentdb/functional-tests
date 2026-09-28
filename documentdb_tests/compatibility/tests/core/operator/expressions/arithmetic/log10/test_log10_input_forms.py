"""Tests for $log10 argument forms, literal input, and nested expression input."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DOUBLE_ZERO

# Property [Argument Form]: $log10 accepts its single argument bare or wrapped in a one-element
# array.
LOG10_ARGUMENT_FORM_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "form_array",
        doc={"value": 1},
        expression={"$log10": ["$value"]},
        expected=DOUBLE_ZERO,
        msg="$log10 should accept its argument wrapped in a one-element array",
    ),
    ExpressionTestCase(
        "form_bare",
        doc={"value": 1},
        expression={"$log10": "$value"},
        expected=DOUBLE_ZERO,
        msg="$log10 should accept its argument without an array wrapper",
    ),
]

# Property [Literal Input]: $log10 evaluates an inline literal argument, not only document fields.
LOG10_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal_input",
        doc={},
        expression={"$log10": [10]},
        expected=1.0,
        msg="$log10 should return one for an inline literal ten",
    ),
]

# Property [Expression Input]: $log10 evaluates a nested expression argument before taking the log.
LOG10_EXPRESSION_INPUT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_multiply",
        doc={},
        expression={"$log10": {"$multiply": [10, 10]}},
        expected=2.0,
        msg="$log10 should evaluate a nested $multiply expression argument",
    ),
]

LOG10_INPUT_FORM_TESTS = (
    LOG10_ARGUMENT_FORM_TESTS + LOG10_LITERAL_TESTS + LOG10_EXPRESSION_INPUT_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(LOG10_INPUT_FORM_TESTS))
def test_log10_input_forms(collection, test_case: ExpressionTestCase):
    """Test $log10 argument form, literal, and nested expression input cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
