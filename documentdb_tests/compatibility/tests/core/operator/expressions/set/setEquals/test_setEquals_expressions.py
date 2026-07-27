"""Tests for $setEquals operand input shapes, inline and resolved via paths and variables."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Inline Operand Input]: literal arrays and expression-operator operands
# evaluate inline without a field reference.
SETEQUALS_INLINE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal",
        expression={"$setEquals": [[1, 2], [2, 1]]},
        expected=True,
        msg="$setEquals should compare literal array inputs",
    ),
    ExpressionTestCase(
        "expression_operator",
        expression={"$setEquals": [{"$literal": [1, 2, 3]}, {"$literal": [3, 2, 1]}]},
        expected=True,
        msg="$setEquals should accept an expression-operator result as an operand",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SETEQUALS_INLINE_TESTS))
def test_setEquals_expression_inline(collection, test):
    """Test $setEquals with inline literal and expression-operator operands."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# Property [Resolved Input Shapes]: operands reached through a shorthand field
# reference, a nested-object path, an array-of-objects path, a numeric-index path,
# or a system variable resolve and feed the operator.
SETEQUALS_INPUT_SHAPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "field_ref_equal",
        doc={"a": [1, 2], "b": [2, 1]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should resolve shorthand field references for both operands",
    ),
    ExpressionTestCase(
        "field_ref_not_equal",
        doc={"a": [1, 2], "b": [3, 4]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should return false for unequal shorthand field references",
    ),
    ExpressionTestCase(
        "nested_object_field",
        doc={"x": {"a": [1, 2]}, "y": {"b": [2, 1]}},
        expression={"$setEquals": ["$x.a", "$y.b"]},
        expected=True,
        msg="$setEquals should resolve nested object field paths for both operands",
    ),
    ExpressionTestCase(
        "composite_array_field",
        doc={"a": [{"b": 1}, {"b": 2}]},
        expression={"$setEquals": ["$a.b", [1, 2]]},
        expected=True,
        msg="$setEquals should resolve a composite array field path through an array of objects",
    ),
    # In an aggregation field path a numeric component is a field name, not an
    # array index, so it resolves to an empty array over the array of arrays,
    # which is not equal to the literal operand.
    ExpressionTestCase(
        "array_index_path",
        doc={"a": [[1, 2], [3]]},
        expression={"$setEquals": ["$a.0", [1, 2]]},
        expected=False,
        msg="$setEquals should resolve a numeric path component to an empty array, yielding false",
    ),
    ExpressionTestCase(
        "deeply_nested_field",
        doc={"a": {"b": {"c": [1, 2]}}, "d": {"e": {"f": [2, 1]}}},
        expression={"$setEquals": ["$a.b.c", "$d.e.f"]},
        expected=True,
        msg="$setEquals should resolve deeply nested field paths for both operands",
    ),
    ExpressionTestCase(
        "root_variable",
        doc={"arr": [1, 2]},
        expression={"$setEquals": ["$$ROOT.arr", [2, 1]]},
        expected=True,
        msg="$setEquals should resolve the ROOT system variable for an array field",
    ),
    ExpressionTestCase(
        "current_variable",
        doc={"arr": [1, 2]},
        expression={"$setEquals": ["$$CURRENT.arr", [2, 1]]},
        expected=True,
        msg="$setEquals should resolve the CURRENT system variable for an array field",
    ),
    ExpressionTestCase(
        "operand_array_of_field_refs",
        doc={"x": 1, "y": 2},
        expression={"$setEquals": [["$x", "$y"], [1, 2]]},
        expected=True,
        msg="$setEquals should resolve an operand array whose elements are field references",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SETEQUALS_INPUT_SHAPE_TESTS))
def test_setEquals_input_shapes(collection, test):
    """Test $setEquals with field-reference, nested, composite, and variable operands."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
