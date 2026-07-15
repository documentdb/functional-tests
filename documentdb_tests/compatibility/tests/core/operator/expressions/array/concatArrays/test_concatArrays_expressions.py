"""
Expression and field path tests for $concatArrays expression.

Tests field path lookups, composite paths, system variables,
and null/missing propagation via expressions.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Field Path]: $concatArrays resolves field-path array arguments.
FIELD_LOOKUP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="nested_field_path",
        expression={"$concatArrays": ["$a.b", "$a.c"]},
        doc={"a": {"b": [1, 2], "c": [3, 4]}},
        expected=[1, 2, 3, 4],
        msg="$concatArrays should resolve nested field paths",
    ),
    ExpressionTestCase(
        id="deeply_nested_field",
        expression={"$concatArrays": ["$a.b.c", "$a.b.d"]},
        doc={"a": {"b": {"c": [10], "d": [20]}}},
        expected=[10, 20],
        msg="$concatArrays should resolve deeply nested field paths",
    ),
    ExpressionTestCase(
        id="nonexistent_field_null",
        expression={"$concatArrays": ["$a.nonexistent", "$b"]},
        doc={"a": {"missing": 1}, "b": [1]},
        expected=None,
        msg="$concatArrays should propagate null for a non-existent field",
    ),
    ExpressionTestCase(
        id="numeric_path_component_not_array_index",
        expression={"$concatArrays": ["$a.0", [5]]},
        doc={"a": [[1, 2], [3, 4]]},
        expected=[5],
        msg="$concatArrays should resolve $a.0 to an empty array in expression context",
    ),
    ExpressionTestCase(
        id="nonexistent_nested_path_empty",
        expression={"$concatArrays": ["$f.x", [3]]},
        doc={"f": [{"g": 1}, {"g": 2}]},
        expected=[3],
        msg="$concatArrays should resolve a non-existent nested path to an empty array",
    ),
    ExpressionTestCase(
        id="nested_array_of_object_path",
        expression={"$concatArrays": ["$a.b.c", [3]]},
        doc={"a": {"b": [{"c": [1]}, {"c": [2]}]}},
        expected=[[1], [2], 3],
        msg="$concatArrays should concatenate an array-of-arrays produced by mapping a field "
        "over an array of objects",
    ),
]

# Property [Composite Path]: $concatArrays resolves composite arrays from dotted paths.
COMPOSITE_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="composite_array",
        expression={"$concatArrays": ["$x.y", [100]]},
        doc={"x": [{"y": 10}, {"y": 20}]},
        expected=[10, 20, 100],
        msg="$concatArrays should resolve a composite array path from an array of objects",
    ),
    ExpressionTestCase(
        id="composite_path_tags",
        expression={"$concatArrays": ["$items.tags", ["d"]]},
        doc={"items": [{"tags": ["a", "b"]}, {"tags": ["c"]}]},
        expected=[["a", "b"], ["c"], "d"],
        msg="$concatArrays should resolve $items.tags to an array of arrays",
    ),
]

# Property [Variables]: $concatArrays works with $let and system variables like $$ROOT.
LET_AND_VARIABLE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="let_variable",
        expression={
            "$let": {
                "vars": {"a": "$arr1", "b": "$arr2"},
                "in": {"$concatArrays": ["$$a", "$$b"]},
            }
        },
        doc={"arr1": [1, 2], "arr2": [3, 4]},
        expected=[1, 2, 3, 4],
        msg="$concatArrays should work with $let variables",
    ),
    ExpressionTestCase(
        id="root_variable",
        expression={"$concatArrays": ["$$ROOT.a", "$$ROOT.b"]},
        doc={"_id": 1, "a": [1], "b": [2]},
        expected=[1, 2],
        msg="$concatArrays should work with $$ROOT",
    ),
    ExpressionTestCase(
        id="current_variable",
        expression={"$concatArrays": ["$$CURRENT.a", "$$CURRENT.b"]},
        doc={"_id": 2, "a": [1], "b": [2]},
        expected=[1, 2],
        msg="$concatArrays should treat $$CURRENT like the field path",
    ),
    ExpressionTestCase(
        id="let_null_variable",
        expression={
            "$let": {
                "vars": {"x": None},
                "in": {"$concatArrays": ["$$x", [1]]},
            }
        },
        doc={"_placeholder": 1},
        expected=None,
        msg="$concatArrays should return null for a null $let variable",
    ),
]

# Property [Null Propagation]: $concatArrays returns null when a field path is null or missing.
NULL_MISSING_EXPR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="missing_field",
        expression={"$concatArrays": ["$nonexistent", [1]]},
        doc={"other": 1},
        expected=None,
        msg="$concatArrays should propagate null for a missing field",
    ),
    ExpressionTestCase(
        id="missing_input_type_is_null",
        expression={"$type": {"$concatArrays": ["$nonexistent", [1]]}},
        doc={"x": 1},
        expected="null",
        msg="$concatArrays should produce null type for a missing field",
    ),
    ExpressionTestCase(
        id="remove_variable",
        expression={"$concatArrays": ["$$REMOVE", [1]]},
        doc={"x": 1},
        expected=None,
        msg="$concatArrays should return null when an argument is $$REMOVE",
    ),
    ExpressionTestCase(
        id="missing_first_field",
        expression={"$concatArrays": ["$a", "$b"]},
        doc={"b": [1]},
        expected=None,
        msg="$concatArrays should return null when the first field is missing",
    ),
    ExpressionTestCase(
        id="missing_last_field",
        expression={"$concatArrays": ["$a", "$b"]},
        doc={"a": [1]},
        expected=None,
        msg="$concatArrays should return null when the last field is missing",
    ),
    ExpressionTestCase(
        id="missing_middle_field",
        expression={"$concatArrays": ["$a", "$b", "$c"]},
        doc={"a": [1], "c": [3]},
        expected=None,
        msg="$concatArrays should return null when a middle field is missing",
    ),
    ExpressionTestCase(
        id="all_missing_fields",
        expression={"$concatArrays": ["$a", "$b"]},
        doc={"_placeholder": 1},
        expected=None,
        msg="$concatArrays should return null when all fields are missing",
    ),
    ExpressionTestCase(
        id="missing_plus_null",
        expression={"$concatArrays": ["$not_a_field", "$null_val"]},
        doc={"null_val": None},
        expected=None,
        msg="$concatArrays should return null for a missing field plus null",
    ),
    ExpressionTestCase(
        id="null_precedes_non_array",
        expression={"$concatArrays": ["$arr", "$null_val", "$int_val"]},
        doc={"arr": [1, 2], "null_val": None, "int_val": 42},
        expected=None,
        msg="$concatArrays should return null when a null precedes a non-array argument",
    ),
    ExpressionTestCase(
        id="null_result_type_is_null",
        expression={"$type": {"$concatArrays": ["$a", "$nonexistent"]}},
        doc={"a": [1]},
        expected="null",
        msg="$concatArrays should produce null type, not missing, for a null result",
    ),
]

# Property [Nesting]: $concatArrays can be nested as an argument to itself.
SELF_COMPOSITION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="nested_concatArrays",
        expression={"$concatArrays": [{"$concatArrays": ["$a", "$b"]}, "$c"]},
        doc={"a": [1], "b": [2], "c": [3]},
        expected=[1, 2, 3],
        msg="$concatArrays should evaluate a nested $concatArrays argument",
    ),
    ExpressionTestCase(
        id="double_nested_concatArrays",
        expression={
            "$concatArrays": [{"$concatArrays": ["$a", "$b"]}, {"$concatArrays": ["$c", "$d"]}]
        },
        doc={"a": [1], "b": [2], "c": [3], "d": [4]},
        expected=[1, 2, 3, 4],
        msg="$concatArrays should evaluate nested $concatArrays in both arguments",
    ),
    ExpressionTestCase(
        id="triple_depth_concatArrays",
        expression={
            "$concatArrays": [{"$concatArrays": [{"$concatArrays": ["$a", "$b"]}, "$c"]}, "$d"]
        },
        doc={"a": [1], "b": [2], "c": [3], "d": [4]},
        expected=[1, 2, 3, 4],
        msg="$concatArrays should evaluate triple-nested $concatArrays",
    ),
]

# Property [Repeated Field]: $concatArrays repeats elements when the same field is referenced again.
SAME_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="same_field_twice",
        expression={"$concatArrays": ["$a", "$a"]},
        doc={"a": [1, 2, 3]},
        expected=[1, 2, 3, 1, 2, 3],
        msg="$concatArrays should double elements when a field is referenced twice",
    ),
    ExpressionTestCase(
        id="same_field_three_times",
        expression={"$concatArrays": ["$a", "$a", "$a"]},
        doc={"a": [1]},
        expected=[1, 1, 1],
        msg="$concatArrays should triple elements when a field is referenced three times",
    ),
    ExpressionTestCase(
        id="self_concat_mixed_types",
        expression={"$concatArrays": ["$a", "$a"]},
        doc={"a": [42, "string", {"key": "value"}, [1, 2], True]},
        expected=[
            42,
            "string",
            {"key": "value"},
            [1, 2],
            True,
            42,
            "string",
            {"key": "value"},
            [1, 2],
            True,
        ],
        msg="$concatArrays should preserve all element types when self-concatenating",
    ),
]

# Property [Expression Inputs]: $concatArrays evaluates array expressions that produce
# array arguments.
# Property [Expression Input]: $concatArrays accepts expression operators as input.
EXPRESSION_INPUT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="array_expression_input",
        expression={"$concatArrays": [["$x", "$y"], [3]]},
        doc={"x": 1, "y": 2},
        expected=[1, 2, 3],
        msg="$concatArrays should resolve an array expression containing field references",
    ),
    ExpressionTestCase(
        id="literal_then_field",
        expression={"$concatArrays": [[1, 2, 3], "$a"]},
        doc={"a": [1, 2]},
        expected=[1, 2, 3, 1, 2],
        msg="$concatArrays should preserve order for a literal followed by a field",
    ),
    ExpressionTestCase(
        id="field_then_literal",
        expression={"$concatArrays": ["$a", [1, 2, 3]]},
        doc={"a": [1, 2]},
        expected=[1, 2, 1, 2, 3],
        msg="$concatArrays should preserve order for a field followed by a literal",
    ),
    ExpressionTestCase(
        id="four_fields_with_empty_and_literal",
        expression={"$concatArrays": ["$a", "$b", "$c", "$d", [], ["array"]]},
        doc={"a": [1, 2], "b": [3, 4], "c": [5, 6], "d": []},
        expected=[1, 2, 3, 4, 5, 6, "array"],
        msg="$concatArrays should concatenate multiple fields and literals",
    ),
]

# Property [Object Elements]: $concatArrays preserves documents with special keys as elements.
SPECIAL_KEY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="special_object_keys",
        expression={"$concatArrays": ["$a", "$b"]},
        doc={"a": [{"a.b": 1}], "b": [{"$x": 2}]},
        expected=[{"a.b": 1}, {"$x": 2}],
        msg="$concatArrays should preserve objects with special keys",
    ),
]

ALL_EXPR_TESTS = (
    FIELD_LOOKUP_TESTS
    + COMPOSITE_PATH_TESTS
    + LET_AND_VARIABLE_TESTS
    + NULL_MISSING_EXPR_TESTS
    + SELF_COMPOSITION_TESTS
    + SAME_FIELD_TESTS
    + EXPRESSION_INPUT_TESTS
    + SPECIAL_KEY_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_EXPR_TESTS))
def test_concatArrays_expression(collection, test):
    """Test $concatArrays with field paths and expressions."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
