"""Tests for $setIntersection operand input shapes, inline and resolved via paths and variables."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import SET_INTERSECTION_NON_ARRAY_ERROR
from documentdb_tests.framework.parametrize import pytest_params

# Property [Inline Operand Input]: literal arrays and expression-operator operands
# evaluate inline without a field reference.
SETINTERSECTION_INLINE_INPUT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal",
        expression={"$setIntersection": [[1, 2, 3], [2, 3, 4]]},
        expected=[2, 3],
        msg="$setIntersection should return intersection for literal array inputs",
    ),
    ExpressionTestCase(
        "expression_operator",
        expression={"$setIntersection": [{"$literal": [1, 2, 3]}, {"$literal": [2, 3, 4]}]},
        expected=[2, 3],
        msg="$setIntersection should accept expression operator inputs like literal",
    ),
]

# Property [Object Operand]: an object operand is not an array and is rejected.
SETINTERSECTION_INLINE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "object_operand",
        expression={"$setIntersection": {"a": [1, 2]}},
        error_code=SET_INTERSECTION_NON_ARRAY_ERROR,
        msg="$setIntersection should return error for an object operand",
    ),
]

SETINTERSECTION_INLINE_TESTS: list[ExpressionTestCase] = (
    SETINTERSECTION_INLINE_INPUT_TESTS + SETINTERSECTION_INLINE_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(SETINTERSECTION_INLINE_TESTS))
def test_setIntersection_expression_inline(collection, test):
    """Test $setIntersection with inline literal and expression-operator operands."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg, ignore_order=True
    )


# Property [Resolved Input Shapes]: operands reached through a nested-object path,
# an array-of-objects path, a numeric-index path, or a system variable resolve and
# feed the operator.
SETINTERSECTION_INPUT_SHAPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_object_field",
        doc={"x": {"a": [1, 2]}, "y": {"b": [2, 3]}},
        expression={"$setIntersection": ["$x.a", "$y.b"]},
        expected=[2],
        msg="$setIntersection should resolve nested object field paths for both operands",
    ),
    ExpressionTestCase(
        "composite_array_field",
        doc={"a": [{"b": 1}, {"b": 2}, {"b": 3}]},
        expression={"$setIntersection": ["$a.b", [2, 3]]},
        expected=[2, 3],
        msg="$setIntersection should resolve composite array field path through array of objects",
    ),
    # In an aggregation field path a numeric component is a field name, not an
    # array index, so it resolves to an empty array over the array of arrays.
    ExpressionTestCase(
        "array_index_path",
        doc={"a": [[1, 2], [3]]},
        expression={"$setIntersection": ["$a.0", [1, 2]]},
        expected=[],
        msg="$setIntersection should resolve a numeric path component to an empty array",
    ),
    ExpressionTestCase(
        "root_variable",
        doc={"arr": [1, 2, 3]},
        expression={"$setIntersection": ["$$ROOT.arr", [2, 3, 4]]},
        expected=[2, 3],
        msg="$setIntersection should resolve ROOT system variable for array field",
    ),
    ExpressionTestCase(
        "current_variable",
        doc={"arr": [1, 2, 3]},
        expression={"$setIntersection": ["$$CURRENT.arr", [2, 3, 4]]},
        expected=[2, 3],
        msg="$setIntersection should resolve CURRENT system variable for array field",
    ),
    ExpressionTestCase(
        "operand_array_of_field_refs",
        doc={"x": 1, "y": 2},
        expression={"$setIntersection": [["$x", "$y"], [2, 3]]},
        expected=[2],
        msg="$setIntersection should resolve an operand array whose elements are field references",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SETINTERSECTION_INPUT_SHAPE_TESTS))
def test_setIntersection_input_shapes(collection, test):
    """Test $setIntersection with nested, composite, numeric-index, and system-variable operands."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg, ignore_order=True)
