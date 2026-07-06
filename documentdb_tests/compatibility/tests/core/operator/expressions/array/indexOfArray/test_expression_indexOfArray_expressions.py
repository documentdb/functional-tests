"""
Expression and field path tests for $indexOfArray expression.

Tests nested expressions, field path lookups, composite paths,
and path through array of objects.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)


# Nested expressions
@pytest.mark.parametrize(
    "expression,expected",
    [
        # 2-level: inner result used as search value
        (
            {
                "$indexOfArray": [
                    [0, 1, 2, 3],
                    {"$indexOfArray": [[10, 20, 30], 30]},
                ]
            },
            2,
        ),
        # 3-level: triple nested, each result feeds the next as search value
        (
            {
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
            1,
        ),
        # 2-level: inner result used as start index
        (
            {
                "$indexOfArray": [
                    [1, 2, 1, 2],
                    1,
                    {"$indexOfArray": [[10, 20, 30], 20]},
                ]
            },
            2,
        ),
    ],
    ids=["nested_2_level", "nested_3_level", "nested_start_index"],
)
def test_indexOfArray_nested_expression(collection, expression, expected):
    """Test $indexOfArray composed with other expressions."""
    result = execute_expression(collection, expression)
    assert_expression_result(result, expected=expected)


# Field path lookups
@pytest.mark.parametrize(
    "document,array_ref,search,expected",
    [
        ({"a": {"b": [10, 20, 30]}}, "$a.b", 20, 1),
        ({"a": {"missing": 1}}, "$a.nonexistent", 0, None),
        ({"a": {"b": {"c": [5, 6, 7]}}}, "$a.b.c", 7, 2),
    ],
    ids=["nested_field_path", "nonexistent_field_null", "deeply_nested_field"],
)
def test_indexOfArray_field_lookup(collection, document, array_ref, search, expected):
    """Test $indexOfArray with field path lookups from inserted documents."""
    result = execute_expression_with_insert(
        collection, {"$indexOfArray": [array_ref, search]}, document
    )
    assert_expression_result(result, expected=expected)


def test_indexOfArray_composite_array_as_array(collection):
    """Test $indexOfArray with composite array from $x.y as the array argument."""
    result = execute_expression_with_insert(
        collection, {"$indexOfArray": ["$x.y", 20]}, {"x": [{"y": 10}, {"y": 20}, {"y": 30}]}
    )
    assert_expression_result(result, expected=1)


def test_indexOfArray_composite_array_as_search(collection):
    """Test $indexOfArray with composite array from $x.y as the search value."""
    result = execute_expression_with_insert(
        collection,
        {"$indexOfArray": [[[10, 20], [30, 40]], "$x.y"]},
        {"x": [{"y": 30}, {"y": 40}]},
    )
    assert_expression_result(result, expected=1)
