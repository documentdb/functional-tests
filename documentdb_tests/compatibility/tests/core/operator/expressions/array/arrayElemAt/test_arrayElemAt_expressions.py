"""
Expression and field path tests for $arrayElemAt expression.

Tests nested expressions, field path lookups, composite paths,
and path through array of objects.
"""

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.test_constants import DECIMAL128_ZERO


# Nested expressions
@pytest.mark.parametrize(
    "expression,expected",
    [
        # 2D array access: arr[1][0]
        ({"$arrayElemAt": [{"$arrayElemAt": [[[10, 20], [30, 40]], 1]}, 0]}, 30),
        # 3D array access: arr[1][0][1]
        (
            {
                "$arrayElemAt": [
                    {
                        "$arrayElemAt": [
                            {"$arrayElemAt": [[[[1, 2], [3, 4]], [[5, 6], [7, 8]]], 1]},
                            0,
                        ]
                    },
                    1,
                ]
            },
            6,
        ),
        # 4D array access: arr[1][1][0][1]
        (
            {
                "$arrayElemAt": [
                    {
                        "$arrayElemAt": [
                            {
                                "$arrayElemAt": [
                                    {
                                        "$arrayElemAt": [
                                            [
                                                [[[1, 2], [3, 4]], [[5, 6], [7, 8]]],
                                                [[[9, 10], [11, 12]], [[13, 14], [15, 16]]],
                                            ],
                                            1,
                                        ]
                                    },
                                    1,
                                ]
                            },
                            0,
                        ]
                    },
                    1,
                ]
            },
            14,
        ),
    ],
    ids=["nested_2d_access", "nested_3d_access", "nested_4d_access"],
)
def test_arrayElemAt_nested_expression(collection, expression, expected):
    """Test $arrayElemAt composed with other expressions."""
    result = execute_expression(collection, expression)
    assert_expression_result(result, expected=expected)


# Field path lookups: $arrayElemAt with array and/or index arguments resolved from inserted
# document fields. These all share one execution path, so they are parametrized into one test.
@pytest.mark.parametrize(
    "document,array_ref,idx,expected",
    [
        ({"a": {"b": [10, 20, 30]}}, "$a.b", 1, 20),
        ({"a": {"missing": 1}}, "$a.nonexistent", 0, None),
        ({"a": {"b": {"c": [5, 6, 7]}}}, "$a.b.c", -1, 7),
        # field path traverses an array of objects -> collapses to [10, 20]
        ({"a": [{"b": 10}, {"b": 20}]}, "$a.b", 0, 10),
        # literal array with a field-path index
        ({"a": {"b": 1}}, [10, 20, 30], "$a.b", 20),
        # array argument resolved from an array of objects
        ({"x": [{"y": 10}, {"y": 20}, {"y": 30}]}, "$x.y", 1, 20),
        # numeric path component ".0" addresses an object key "0", not an array position
        ({"a": {"0": {"b": [10, 20, 30]}}}, "$a.0.b", 1, 20),
        # Decimal128 index resolved alongside a composite array path
        ({"a": [{"b": 1}, {"b": 2}, {"b": 3}]}, "$a.b", DECIMAL128_ZERO, 1),
        ({"a": [{"b": 1}, {"b": 2}, {"b": 3}]}, "$a.b", Decimal128("-1"), 3),
        # first argument is an array expression whose elements are field references
        ({"x": 10, "y": 20}, ["$x", "$y"], 0, 10),
        ({"x": 10, "y": 20}, ["$x", "$y"], 1, 20),
        ({"x": 10, "y": 20}, ["$x", "$y"], -1, 20),
    ],
    ids=[
        "nested_field_path",
        "nonexistent_field_null",
        "deeply_nested_field",
        "path_through_array_of_objects",
        "composite_path_for_index",
        "composite_array_as_array",
        "object_numeric_key_path",
        "composite_decimal128_pos",
        "composite_decimal128_neg",
        "array_expr_first",
        "array_expr_second",
        "array_expr_negative",
    ],
)
def test_arrayElemAt_field_lookup(collection, document, array_ref, idx, expected):
    """Test $arrayElemAt with array/index arguments resolved from inserted document fields."""
    result = execute_expression_with_insert(
        collection, {"$arrayElemAt": [array_ref, idx]}, document
    )
    assert_expression_result(result, expected=expected)


# Field-path lookups that resolve to a missing result: an out-of-bounds Decimal128 index, or a
# numeric path component that does not positionally index an array. Same execution path -> one test.
@pytest.mark.parametrize(
    "document,array_ref,idx",
    [
        ({"a": [{"b": 1}, {"b": 2}, {"b": 3}]}, "$a.b", Decimal128("4")),
        ({"a": [{"b": 1}, {"b": 2}, {"b": 3}]}, "$a.b", Decimal128("-4")),
        # "$a.0" does not positionally index an array in expression context -> missing
        ({"a": [[1, 2], [3, 4]]}, "$a.0", 0),
    ],
    ids=[
        "composite_decimal128_oob_pos",
        "composite_decimal128_oob_neg",
        "numeric_path_component_not_array_index",
    ],
)
def test_arrayElemAt_field_lookup_missing(collection, document, array_ref, idx):
    """Test $arrayElemAt returns a missing result for out-of-bounds field-path lookups."""
    result = execute_expression_with_insert(
        collection, {"$arrayElemAt": [array_ref, idx]}, document
    )
    assertSuccess(result, [{}])
