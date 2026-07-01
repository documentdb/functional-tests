import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR

# Array expression tests: $bitAnd where the first operand is an array expression
ARRAY_EXPRESSION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "array_expression",
        expression={"$bitAnd": [["$a", "$b"], 3]},
        doc={"a": 1, "b": 3},
        error_code=TYPE_MISMATCH_ERROR,
        msg="$bitAnd should reject an array expression as first operand",
    ),
]

# Object expression tests: $bitAnd where the first operand is an object expression
OBJECT_EXPRESSION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "object_expression",
        expression={"$bitAnd": [{"x": "$a", "y": "$b"}, 0]},
        doc={"a": 1, "b": 3},
        error_code=TYPE_MISMATCH_ERROR,
        msg="$bitAnd should reject an object expression as an input",
    ),
]

ALL_ADDITIONAL_TESTS = ARRAY_EXPRESSION_TESTS + OBJECT_EXPRESSION_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_ADDITIONAL_TESTS))
def test_bitAnd_expression_additional(collection, test):
    """Test $bitAnd with array and object expression inputs."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
