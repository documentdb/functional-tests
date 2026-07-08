"""Tests for $ceil argument forms: array-wrapped, bare, literal, and nested expression inputs."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Argument Form]: $ceil accepts its single argument bare or wrapped in a one-element
# array.
CEIL_ARGUMENT_FORM_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "form_array",
        doc={"value": 1.5},
        expression={"$ceil": ["$value"]},
        expected=2.0,
        msg="$ceil should accept its argument wrapped in a one-element array",
    ),
    ExpressionTestCase(
        "form_bare",
        doc={"value": 1.5},
        expression={"$ceil": "$value"},
        expected=2.0,
        msg="$ceil should accept its argument without an array wrapper",
    ),
]

# Property [Literal Input]: $ceil evaluates an inline literal argument, not only document fields.
CEIL_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal_input",
        doc={},
        expression={"$ceil": [4.1]},
        expected=5.0,
        msg="$ceil should return the ceiling of an inline literal argument",
    ),
]

# Property [Expression Input]: $ceil evaluates a nested expression argument before rounding up.
CEIL_EXPRESSION_INPUT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_ceil",
        doc={"value": 4.1},
        expression={"$ceil": {"$ceil": "$value"}},
        expected=5.0,
        msg="$ceil should evaluate a nested $ceil expression argument",
    ),
    ExpressionTestCase(
        "object_expression_input",
        doc={"value": 1.5},
        expression={"$ceil": {"$multiply": ["$value", 1.0]}},
        expected=2.0,
        msg="$ceil should accept an object expression as its argument",
    ),
]

CEIL_INPUT_FORM_ALL_TESTS = (
    CEIL_ARGUMENT_FORM_TESTS + CEIL_LITERAL_TESTS + CEIL_EXPRESSION_INPUT_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(CEIL_INPUT_FORM_ALL_TESTS))
def test_ceil_input_forms(collection, test_case: ExpressionTestCase):
    """Test $ceil argument form, literal, and nested expression input cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
