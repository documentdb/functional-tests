"""
Expression and field path tests for $indexOfArray expression.

Tests nested expressions, field path lookups, composite paths,
and path through array of objects.
"""

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

# Property [Nested Expressions]: $indexOfArray evaluates nested expressions as arguments.
NESTED_EXPRESSION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_2_level",
        expression={
            "$indexOfArray": [
                [0, 1, 2, 3],
                {"$indexOfArray": [[10, 20, 30], 30]},
            ]
        },
        expected=2,
        msg="$indexOfArray should use inner result as search value",
    ),
    ExpressionTestCase(
        "nested_3_level",
        expression={
            "$indexOfArray": [
                [0, 1, 2],
                {
                    "$indexOfArray": [
                        [0, 1, 2],
                        {"$indexOfArray": [[5, 10, 15], 10]},
                    ]
                },
            ]
        },
        expected=1,
        msg="$indexOfArray should support triple nested composition",
    ),
    ExpressionTestCase(
        "nested_start_index",
        expression={
            "$indexOfArray": [
                [1, 2, 1, 2],
                1,
                {"$indexOfArray": [[10, 20, 30], 20]},
            ]
        },
        expected=2,
        msg="$indexOfArray should use nested result as start index",
    ),
]

# Property [Field Path Resolution]: $indexOfArray resolves nested and deeply nested field paths.
FIELD_LOOKUP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_field_path",
        expression={"$indexOfArray": ["$a.b", 20]},
        doc={"a": {"b": [10, 20, 30]}},
        expected=1,
        msg="$indexOfArray should resolve nested field path as array",
    ),
    ExpressionTestCase(
        "nonexistent_field_null",
        expression={"$indexOfArray": ["$a.nonexistent", 0]},
        doc={"a": {"missing": 1}},
        expected=None,
        msg="$indexOfArray should return null for non-existent field",
    ),
    ExpressionTestCase(
        "deeply_nested_field",
        expression={"$indexOfArray": ["$a.b.c", 7]},
        doc={"a": {"b": {"c": [5, 6, 7]}}},
        expected=2,
        msg="$indexOfArray should resolve deeply nested field path",
    ),
]

# Property [Composite Paths]: $indexOfArray resolves composite array paths from array-of-objects.
COMPOSITE_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "composite_array_as_array",
        expression={"$indexOfArray": ["$x.y", 20]},
        doc={"x": [{"y": 10}, {"y": 20}, {"y": 30}]},
        expected=1,
        msg="$indexOfArray should find value in composite array path",
    ),
    ExpressionTestCase(
        "composite_array_as_search",
        expression={"$indexOfArray": [[[10, 20], [30, 40]], "$x.y"]},
        doc={"x": [{"y": 30}, {"y": 40}]},
        expected=1,
        msg="$indexOfArray should match composite array as search value",
    ),
]

ALL_EXPRESSION_TESTS = NESTED_EXPRESSION_TESTS + FIELD_LOOKUP_TESTS + COMPOSITE_PATH_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_EXPRESSION_TESTS))
def test_indexOfArray_expression(collection, test):
    """Test $indexOfArray with expressions, field paths, and composite paths."""
    if test.doc is None:
        result = execute_expression(collection, test.expression)
    else:
        result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
