"""Tests for $setDifference operand input shapes, inline and resolved via paths and variables."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import EXPRESSION_TYPE_MISMATCH_ERROR
from documentdb_tests.framework.parametrize import pytest_params

# Property [Inline Operand Input]: literal arrays and expression-operator operands
# evaluate inline without a field reference.
SETDIFFERENCE_INLINE_INPUT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal",
        expression={"$setDifference": [["a", "b", "c"], ["b"]]},
        expected=["a", "c"],
        msg="Should return difference for literal array inputs",
    ),
    ExpressionTestCase(
        "expression_operator",
        expression={"$setDifference": [{"$literal": [1, 2, 3]}, {"$literal": [2, 3]}]},
        expected=[1],
        msg="Should accept expression operator inputs like literal",
    ),
]

# Property [Operand Structure]: an operand list that is not two arrays is rejected.
SETDIFFERENCE_INLINE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "array_expression_input",
        expression={"$setDifference": [["$arr1", "$arr2"]]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should return error for single array argument",
    ),
    ExpressionTestCase(
        "object_expression_input",
        expression={"$setDifference": {"a": "$arr1"}},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should return error for object expression input",
    ),
]

SETDIFFERENCE_INLINE_TESTS: list[ExpressionTestCase] = (
    SETDIFFERENCE_INLINE_INPUT_TESTS + SETDIFFERENCE_INLINE_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(SETDIFFERENCE_INLINE_TESTS))
def test_setDifference_expression_inline(collection, test):
    """Test $setDifference with inline literal and expression-operator operands."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


# Property [Resolved Input Shapes]: operands reached through a nested-object path,
# an array-of-objects path, a numeric-index path, or a system variable resolve and
# feed the operator.
SETDIFFERENCE_INPUT_SHAPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_object_field",
        doc={"a": {"b": [1, 2, 3]}},
        expression={"$setDifference": ["$a.b", [2]]},
        expected=[1, 3],
        msg="Should resolve nested object field path for first array",
    ),
    ExpressionTestCase(
        "composite_array_field",
        doc={"a": [{"b": 1}, {"b": 2}]},
        expression={"$setDifference": ["$a.b", [1]]},
        expected=[2],
        msg="Should resolve composite array field path through array of objects",
    ),
    # In an aggregation field path a numeric component is a field name, not an
    # array index, so it resolves to an empty array over the array of arrays.
    ExpressionTestCase(
        "array_index_path",
        doc={"a": [[1, 2], [3]]},
        expression={"$setDifference": ["$a.0", []]},
        expected=[],
        msg="Should resolve numeric path component to an empty array in aggregation context",
    ),
    ExpressionTestCase(
        "root_variable",
        doc={"arr": [1, 2]},
        expression={"$setDifference": ["$$ROOT.arr", [2]]},
        expected=[1],
        msg="Should resolve ROOT system variable for array field",
    ),
    ExpressionTestCase(
        "current_variable",
        doc={"arr": [1, 2]},
        expression={"$setDifference": ["$$CURRENT.arr", [2]]},
        expected=[1],
        msg="Should resolve CURRENT system variable for array field",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SETDIFFERENCE_INPUT_SHAPE_TESTS))
def test_setDifference_input_shapes(collection, test):
    """Test $setDifference with nested, composite, numeric-index, and system-variable operands."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
