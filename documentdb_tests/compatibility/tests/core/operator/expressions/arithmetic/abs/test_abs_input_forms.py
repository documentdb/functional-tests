import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Argument Form]: $abs accepts its single argument bare or wrapped in a one-element
# array.
ABS_ARGUMENT_FORM_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "form_array",
        doc={"value": -5},
        expression={"$abs": ["$value"]},
        expected=5,
        msg="$abs should accept its argument wrapped in a one-element array",
    ),
    ExpressionTestCase(
        "form_bare",
        doc={"value": -5},
        expression={"$abs": "$value"},
        expected=5,
        msg="$abs should accept its argument without an array wrapper",
    ),
]

# Property [Literal Input]: $abs evaluates an inline literal argument, not only document fields.
ABS_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal_input",
        doc={},
        expression={"$abs": [-5]},
        expected=5,
        msg="$abs should return the absolute value of an inline literal argument",
    ),
]

# Property [Expression Input]: $abs evaluates a nested expression argument before taking the
# absolute value.
ABS_EXPRESSION_INPUT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_abs",
        doc={"value": -4},
        expression={"$abs": {"$abs": "$value"}},
        expected=4,
        msg="$abs should evaluate a nested $abs expression argument",
    ),
]

ABS_INPUT_FORM_TESTS = ABS_ARGUMENT_FORM_TESTS + ABS_LITERAL_TESTS + ABS_EXPRESSION_INPUT_TESTS


@pytest.mark.parametrize("test_case", pytest_params(ABS_INPUT_FORM_TESTS))
def test_abs_input_forms(collection, test_case: ExpressionTestCase):
    """Test $abs argument form, literal, and nested expression input cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
