import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Expression Input]: $add evaluates a nested expression argument before summing.
ADD_EXPRESSION_INPUT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_add",
        doc={"a": 1, "b": 2},
        expression={"$add": [{"$add": ["$a", "$b"]}, 3]},
        expected=6,
        msg="$add should evaluate a nested $add expression as an operand",
    ),
]

# Property [Mixed Literal and Field]: $add accepts a mix of field references and inline literals
# in the same operand list.
ADD_MIXED_INPUT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "mixed_literal_and_field",
        doc={"a": 10},
        expression={"$add": ["$a", 5]},
        expected=15,
        msg="$add should sum a field reference and an inline literal operand",
    ),
]

ADD_INPUT_FORM_ALL_TESTS = ADD_EXPRESSION_INPUT_TESTS + ADD_MIXED_INPUT_TESTS


@pytest.mark.parametrize("test_case", pytest_params(ADD_INPUT_FORM_ALL_TESTS))
def test_add_input_forms(collection, test_case: ExpressionTestCase):
    """Test $add literal, nested expression, and mixed input form cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
