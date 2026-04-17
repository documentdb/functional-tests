"""Tests for $cond nesting and composition — nested $cond chains, $isArray guard pattern,
and nested document field path traversal."""

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

NESTED_OBJ_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_in_if",
        expression={
            "$cond": {
                "if": {"$cond": {"if": True, "then": False, "else": True}},
                "then": "outer-then",
                "else": "outer-else",
            }
        },
        expected="outer-else",
        msg="Nested $cond in if — inner returns false, takes outer else",
    ),
    ExpressionTestCase(
        "nested_in_then",
        expression={
            "$cond": {
                "if": True,
                "then": {"$cond": {"if": True, "then": "inner-then", "else": "inner-else"}},
                "else": "outer-else",
            }
        },
        expected="inner-then",
        msg="Nested $cond in then",
    ),
    ExpressionTestCase(
        "nested_in_else",
        expression={
            "$cond": {
                "if": False,
                "then": "outer-then",
                "else": {"$cond": {"if": False, "then": "inner-then", "else": "inner-else"}},
            }
        },
        expected="inner-else",
        msg="Nested $cond in else",
    ),
    ExpressionTestCase(
        "3_level_chain",
        expression={
            "$cond": {
                "if": False,
                "then": "L1",
                "else": {
                    "$cond": {
                        "if": False,
                        "then": "L2",
                        "else": {"$cond": {"if": True, "then": "L3", "else": "L4"}},
                    }
                },
            }
        },
        expected="L3",
        msg="3-level chain",
    ),
]

NESTED_ARR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "arr_cond_in_all_positions",
        expression={
            "$cond": [
                {"$cond": [True, True, False]},
                {"$cond": [True, 1, 2]},
                {"$cond": [True, 3, 4]},
            ]
        },
        expected=1,
        msg="$cond in if/then/else positions",
    ),
    ExpressionTestCase(
        "arr_outer_false",
        expression={
            "$cond": [
                {"$cond": [False, True, False]},
                {"$cond": [True, 1, 2]},
                {"$cond": [False, 3, 4]},
            ]
        },
        expected=4,
        msg="outer false → else branch evaluated",
    ),
    ExpressionTestCase(
        "arr_3_level",
        expression={
            "$cond": [
                {"$cond": [False, True, False]},
                {"$cond": [True, 1, 2]},
                {"$cond": [True, {"$cond": [True, 5, 6]}, {"$cond": [True, 7, 8]}]},
            ]
        },
        expected=5,
        msg="3-level deep nesting in array syntax",
    ),
]

LITERAL_ONLY_TESTS = NESTED_OBJ_TESTS + NESTED_ARR_TESTS


@pytest.mark.parametrize("test", pytest_params(LITERAL_ONLY_TESTS))
def test_cond_nesting_literal(collection, test):
    """Test $cond nesting and composition with literal/no-doc expressions."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


ISARRAY_COND_EXPRESSION = {
    "$cond": {
        "if": {"$isArray": "$tags"},
        "then": {"$size": "$tags"},
        "else": 0,
    }
}

ISARRAY_COND_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "isArray_with_array",
        expression=ISARRAY_COND_EXPRESSION,
        doc={"tags": ["a", "b", "c"]},
        expected=3,
        msg="$isArray true for array field — $size returns count",
    ),
    ExpressionTestCase(
        "isArray_with_empty_array",
        expression=ISARRAY_COND_EXPRESSION,
        doc={"tags": []},
        expected=0,
        msg="$isArray true for empty array — $size returns 0",
    ),
    ExpressionTestCase(
        "isArray_with_string",
        expression=ISARRAY_COND_EXPRESSION,
        doc={"tags": "not-an-array"},
        expected=0,
        msg="$isArray false for string — returns else branch 0",
    ),
    ExpressionTestCase(
        "isArray_with_missing_field",
        expression=ISARRAY_COND_EXPRESSION,
        doc={"other": 1},
        expected=0,
        msg="$isArray false for missing field — returns else branch 0",
    ),
    ExpressionTestCase(
        "isArray_with_null",
        expression=ISARRAY_COND_EXPRESSION,
        doc={"tags": None},
        expected=0,
        msg="$isArray false for null — returns else branch 0",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ISARRAY_COND_TESTS))
def test_cond_isarray_guard(collection, test):
    """Test $cond with $isArray to conditionally apply $size."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


NESTED_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "deep_dot_path",
        expression={"$cond": [{"$gt": ["$a.b.c.d", 0]}, "found", "missing"]},
        doc={"a": {"b": [{"c": [{"d": 1}]}]}},
        expected="found",
        msg="$cond resolves deeply nested dot path through arrays",
    ),
    ExpressionTestCase(
        "numeric_index_path",
        expression={"$cond": [{"$gt": ["$a.0.b", 0]}, "first", "other"]},
        doc={"a": [{"b": 1}, {"b": 2}]},
        expected="first",
        msg="$cond resolves numeric-indexed array path $a.0.b",
    ),
    ExpressionTestCase(
        "deep_path_missing",
        expression={"$cond": [{"$gt": ["$a.b.c.d", 0]}, "found", "missing"]},
        doc={"a": {"b": {"x": 1}}},
        expected="missing",
        msg="$cond takes else when nested path doesn't resolve",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NESTED_PATH_TESTS))
def test_cond_nested_field_paths(collection, test):
    """Test $cond with deeply nested and numeric-indexed field paths."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
