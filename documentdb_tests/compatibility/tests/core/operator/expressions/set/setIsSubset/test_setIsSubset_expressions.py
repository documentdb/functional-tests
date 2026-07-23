"""Tests for $setIsSubset operand input shapes, inline and resolved via paths and variables."""

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
SETISSUBSET_INLINE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal",
        expression={"$setIsSubset": [["a", "b"], ["a", "b", "c"]]},
        expected=True,
        msg="$setIsSubset should compare literal array inputs",
    ),
    ExpressionTestCase(
        "literal_expression_operator",
        expression={"$setIsSubset": [{"$literal": [1, 2]}, {"$literal": [1, 2, 3]}]},
        expected=True,
        msg="$setIsSubset should accept a $literal expression result as an operand",
    ),
    ExpressionTestCase(
        "nested_set_operator",
        expression={"$setIsSubset": [{"$setUnion": [[1, 2], [3]]}, [1, 2, 3]]},
        expected=True,
        msg="$setIsSubset should accept a nested set-operator result as an operand",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SETISSUBSET_INLINE_TESTS))
def test_setIsSubset_expression_inline(collection, test):
    """Test $setIsSubset with inline literal and expression-operator operands."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# Property [Resolved Input Shapes]: operands reached through a shorthand field
# reference, a nested-object path, an array-of-objects path, a numeric-index path,
# an operand array of field references, or a system variable resolve and feed the
# operator.
SETISSUBSET_INPUT_SHAPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "field_ref_subset",
        doc={"a": [10, 20], "b": [10, 20, 30]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should resolve shorthand field references for both operands",
    ),
    ExpressionTestCase(
        "field_ref_not_subset",
        doc={"a": [10, 20], "b": [20, 30]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for unequal shorthand field references",
    ),
    ExpressionTestCase(
        "nested_object_field",
        doc={"a": {"b": [1, 2]}, "c": {"d": [1, 2, 3]}},
        expression={"$setIsSubset": ["$a.b", "$c.d"]},
        expected=True,
        msg="$setIsSubset should resolve nested object field paths for both operands",
    ),
    ExpressionTestCase(
        "composite_array_field",
        doc={"a": [{"b": 1}, {"b": 2}]},
        expression={"$setIsSubset": ["$a.b", [1, 2, 3]]},
        expected=True,
        msg="$setIsSubset should resolve a composite array field path through an array of objects",
    ),
    # In an aggregation field path a numeric component is a field name, not an
    # array index, so it resolves to an empty array over the array of arrays.
    # An empty first operand is a subset of any set.
    ExpressionTestCase(
        "array_index_path_first",
        doc={"a": [[1, 2], [3]]},
        expression={"$setIsSubset": ["$a.0", [1, 2]]},
        expected=True,
        msg="$setIsSubset should treat a numeric path component as an empty first operand (true)",
    ),
    # The same empty resolution as a non-empty second operand's superset makes a
    # non-empty first operand fail the subset check.
    ExpressionTestCase(
        "array_index_path_second",
        doc={"a": [[1, 2], [3]]},
        expression={"$setIsSubset": [[1, 2], "$a.0"]},
        expected=False,
        msg="$setIsSubset should treat a numeric path component as an empty second operand (false)",
    ),
    ExpressionTestCase(
        "operand_array_of_field_refs",
        doc={"x": 1, "y": 2},
        expression={"$setIsSubset": [["$x", "$y"], [1, 2, 3]]},
        expected=True,
        msg="$setIsSubset should resolve an operand array whose elements are field references",
    ),
    ExpressionTestCase(
        "deeply_nested_field",
        doc={"a": {"b": {"c": [1, 2]}}, "d": {"e": {"f": [1, 2, 3]}}},
        expression={"$setIsSubset": ["$a.b.c", "$d.e.f"]},
        expected=True,
        msg="$setIsSubset should resolve deeply nested field paths for both operands",
    ),
    ExpressionTestCase(
        "root_variable",
        doc={"arr": [1, 2]},
        expression={"$setIsSubset": ["$$ROOT.arr", [1, 2, 3]]},
        expected=True,
        msg="$setIsSubset should resolve the ROOT system variable for an array field",
    ),
    ExpressionTestCase(
        "current_variable",
        doc={"arr": [1, 2]},
        expression={"$setIsSubset": ["$$CURRENT.arr", [1, 2, 3]]},
        expected=True,
        msg="$setIsSubset should resolve the CURRENT system variable for an array field",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SETISSUBSET_INPUT_SHAPE_TESTS))
def test_setIsSubset_input_shapes(collection, test):
    """Test $setIsSubset with field-reference, nested, composite, index, and variable operands."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
