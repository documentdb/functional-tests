"""
Expression and field path tests for $zip expression.

Tests field path lookups, composite paths, system variables,
and null/missing propagation via expressions.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    execute_expression_with_insert,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import ZIP_REQUIRES_ARRAY_ELEMENT_ERROR
from documentdb_tests.framework.parametrize import pytest_params

# ---------------------------------------------------------------------------
# Field path lookups
# ---------------------------------------------------------------------------
FIELD_LOOKUP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="nested_field_path",
        expression={"$zip": {"inputs": ["$a.b", "$a.c"]}},
        doc={"a": {"b": [1, 2], "c": [3, 4]}},
        expected=[[1, 3], [2, 4]],
        msg="Should resolve nested field paths",
    ),
    ExpressionTestCase(
        id="deeply_nested_field",
        expression={"$zip": {"inputs": ["$a.b.c", "$a.b.d"]}},
        doc={"a": {"b": {"c": [10], "d": [20]}}},
        expected=[[10, 20]],
        msg="Should resolve deeply nested field paths",
    ),
    ExpressionTestCase(
        id="nonexistent_field_null",
        expression={"$zip": {"inputs": ["$a.nonexistent", "$b"]}},
        doc={"a": {"missing": 1}, "b": [1]},
        expected=None,
        msg="Non-existent field should propagate null",
    ),
    ExpressionTestCase(
        id="same_field_twice",
        expression={"$zip": {"inputs": ["$arr", "$arr"]}},
        doc={"arr": [1, 2, 3]},
        expected=[[1, 1], [2, 2], [3, 3]],
        msg="Same field used twice should zip with itself",
    ),
]

# ---------------------------------------------------------------------------
# Composite array paths
# ---------------------------------------------------------------------------
COMPOSITE_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="composite_array",
        expression={"$zip": {"inputs": ["$x.y", "$x.z"]}},
        doc={"x": [{"y": 1, "z": 10}, {"y": 2, "z": 20}]},
        expected=[[1, 10], [2, 20]],
        msg="Composite array path from array-of-objects",
    ),
    ExpressionTestCase(
        id="array_index_path_resolves_empty",
        expression={"$zip": {"inputs": ["$a.0", [1, 2]]}},
        doc={"a": [[1, 2], [3, 4]]},
        expected=[],
        msg="Array index path resolves to [] (shortest)",
    ),
]

# ---------------------------------------------------------------------------
# $let and system variables
# ---------------------------------------------------------------------------
LET_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="let_variable",
        expression={
            "$let": {
                "vars": {"a": "$arr1", "b": "$arr2"},
                "in": {"$zip": {"inputs": ["$$a", "$$b"]}},
            }
        },
        doc={"arr1": [1, 2], "arr2": [3, 4]},
        expected=[[1, 3], [2, 4]],
        msg="Should work with $let variables",
    ),
    ExpressionTestCase(
        id="root_variable",
        expression={"$zip": {"inputs": ["$$ROOT.a", "$$ROOT.b"]}},
        doc={"_id": 1, "a": [1], "b": [2]},
        expected=[[1, 2]],
        msg="Should work with $$ROOT",
    ),
    ExpressionTestCase(
        id="current_variable",
        expression={"$zip": {"inputs": ["$$CURRENT.a", "$$CURRENT.b"]}},
        doc={"_id": 2, "a": [1], "b": [2]},
        expected=[[1, 2]],
        msg="$$CURRENT should be equivalent to field path",
    ),
]

# ---------------------------------------------------------------------------
# Null/missing via expression
# ---------------------------------------------------------------------------
NULL_MISSING_EXPR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="missing_field",
        expression={"$zip": {"inputs": ["$nonexistent", [1]]}},
        doc={"other": 1},
        expected=None,
        msg="Missing field should propagate null",
    ),
    ExpressionTestCase(
        id="missing_input_type_is_null",
        expression={"$type": {"$zip": {"inputs": ["$nonexistent", [1]]}}},
        doc={"x": 1},
        expected="null",
        msg="Missing field should produce null type",
    ),
    ExpressionTestCase(
        id="remove_variable",
        expression={"$zip": {"inputs": ["$$REMOVE", [1]]}},
        doc={"x": 1},
        expected=None,
        msg="$$REMOVE propagates null",
    ),
    ExpressionTestCase(
        id="field_ref_non_array",
        expression={"$zip": {"inputs": ["$a", [1]]}},
        doc={"a": 1},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Field resolving to non-array should error",
    ),
    ExpressionTestCase(
        id="missing_first_input",
        expression={"$zip": {"inputs": ["$missing", [1, 2]]}},
        doc={"a": 1},
        expected=None,
        msg="Missing first input returns null",
    ),
    ExpressionTestCase(
        id="all_missing_fields",
        expression={"$zip": {"inputs": ["$x", "$y"]}},
        doc={"_placeholder": 1},
        expected=None,
        msg="All missing fields return null",
    ),
    ExpressionTestCase(
        id="explicit_null_field",
        expression={"$zip": {"inputs": ["$a", "$b"]}},
        doc={"a": None, "b": [1, 2]},
        expected=None,
        msg="Explicit null field returns null",
    ),
    ExpressionTestCase(
        id="null_with_longest_true",
        expression={"$zip": {"inputs": ["$a", [1, 2]], "useLongestLength": True}},
        doc={"a": None},
        expected=None,
        msg="Null input with longest true returns null",
    ),
    ExpressionTestCase(
        id="null_with_defaults",
        expression={
            "$zip": {"inputs": ["$a", [1, 2]], "useLongestLength": True, "defaults": [0, 0]}
        },
        doc={"a": None},
        expected=None,
        msg="Null input with defaults still returns null",
    ),
    ExpressionTestCase(
        id="missing_field_as_element",
        expression={"$zip": {"inputs": [["$not_exist", 2], [1, 2]]}},
        doc={"a": 1},
        expected=[[None, 1], [2, 2]],
        msg="Missing field as element becomes null",
    ),
]

# ---------------------------------------------------------------------------
# Self-composition
# ---------------------------------------------------------------------------
SELF_COMPOSITION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="nested_zip_full",
        expression={
            "$zip": {
                "inputs": [
                    {"$zip": {"inputs": ["$a", "$b"]}},
                    "$c",
                ]
            }
        },
        doc={"a": [1, 2], "b": [3, 4], "c": ["x", "y"]},
        expected=[[[1, 3], "x"], [[2, 4], "y"]],
        msg="Nested $zip as input works correctly",
    ),
]

# ---------------------------------------------------------------------------
# Field path as element in input array
# ---------------------------------------------------------------------------
FIELD_PATH_ELEMENT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="field_path_as_element",
        expression={"$zip": {"inputs": [["$a", "$b"], [1, 2]]}},
        doc={"a": 10, "b": 20},
        expected=[[10, 1], [20, 2]],
        msg="Field paths as elements resolve correctly",
    ),
    ExpressionTestCase(
        id="nested_field_path_as_element",
        expression={"$zip": {"inputs": [["$foo.bar", "$b"], [1, 2]]}},
        doc={"foo": {"bar": 10}, "b": 20},
        expected=[[10, 1], [20, 2]],
        msg="Nested field path as element resolves correctly",
    ),
    ExpressionTestCase(
        id="field_path_in_defaults",
        expression={
            "$zip": {"inputs": ["$a", "$b"], "useLongestLength": True, "defaults": ["$c", "$d"]}
        },
        doc={"a": [1, 2, 3], "b": ["x"], "c": "default_a", "d": "default_b"},
        expected=[[1, "x"], [2, "default_b"], [3, "default_b"]],
        msg="Field paths in defaults resolve from document",
    ),
]

# ---------------------------------------------------------------------------
# Aggregate and test
# ---------------------------------------------------------------------------
ALL_EXPR_TESTS = (
    FIELD_LOOKUP_TESTS
    + COMPOSITE_PATH_TESTS
    + LET_TESTS
    + NULL_MISSING_EXPR_TESTS
    + SELF_COMPOSITION_TESTS
    + FIELD_PATH_ELEMENT_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_EXPR_TESTS))
def test_zip_expression(collection, test):
    """Test $zip with field paths and expressions."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assertResult(result, expected=test.expected, error_code=test.error_code, msg=test.msg)
