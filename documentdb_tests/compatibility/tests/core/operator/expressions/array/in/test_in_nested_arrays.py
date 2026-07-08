"""
Nested array search tests for $in expression.

Tests searching for complex elements in nested mixed arrays and deeply nested structures.
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, MaxKey, MinKey, ObjectId

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Success: nested mixed arrays as search targets
NESTED_MIXED_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_find_object_in_mixed",
        doc={"val": {"a": 1}, "arr": [1, "two", {"a": 1}, [3, 4], True]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find object in nested mixed array",
    ),
    ExpressionTestCase(
        "nested_find_array_in_mixed",
        doc={"val": [3, 4], "arr": [1, "two", {"a": 1}, [3, 4], True]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find array in nested mixed array",
    ),
    ExpressionTestCase(
        "nested_find_deep_object",
        doc={"val": {"a": {"b": 3}}, "arr": [[1, 2], {"a": {"b": 3}}, "x"]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find deep object in array",
    ),
    ExpressionTestCase(
        "nested_find_array_with_mixed_types",
        doc={"val": [None, "a", 2], "arr": [1, [None, "a", 2], "b"]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find mixed-type subarray",
    ),
    ExpressionTestCase(
        "nested_find_empty_object",
        doc={"val": {}, "arr": [1, {}, [2], "a"]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find empty object in array",
    ),
    ExpressionTestCase(
        "nested_find_empty_array",
        doc={"val": [], "arr": [1, {}, [], "a"]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find empty array in array",
    ),
    ExpressionTestCase(
        "nested_find_subarray_binary_decimal128",
        doc={
            "val": [Binary(b"\x01\x02", 0), Decimal128("3.14")],
            "arr": [1, [Binary(b"\x01\x02", 0), Decimal128("3.14")], "x", [3]],
        },
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find subarray with binary and decimal128",
    ),
    ExpressionTestCase(
        "nested_find_subarray_object_array",
        doc={"val": [{"k": 1}, [2, 3]], "arr": ["a", [{"k": 1}, [2, 3]], None, 4]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find subarray with object and array",
    ),
    ExpressionTestCase(
        "nested_find_subarray_datetime_objectid",
        doc={
            "val": [
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                ObjectId("000000000000000000000001"),
            ],
            "arr": [
                0,
                [datetime(2024, 1, 1, tzinfo=timezone.utc), ObjectId("000000000000000000000001")],
                "end",
            ],
        },
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find subarray with datetime and objectid",
    ),
    ExpressionTestCase(
        "nested_find_subarray_minkey_maxkey",
        doc={"val": [MinKey(), MaxKey()], "arr": [[MinKey(), MaxKey()], 1, "a"]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find subarray with minkey and maxkey",
    ),
]

# Success: deeply nested search targets (3-5 levels)
DEEPLY_NESTED_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_3_levels",
        doc={"val": [[2, 3], [4, 5]], "arr": [1, [[2, 3], [4, 5]], "end"]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find 3-level nested array",
    ),
    ExpressionTestCase(
        "nested_4_levels",
        doc={"val": [[[1, 2], 3], 4], "arr": ["a", [[[1, 2], 3], 4], None]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find 4-level nested array",
    ),
    ExpressionTestCase(
        "nested_deep_mixed_bson",
        doc={
            "val": [[MinKey(), {"a": [Decimal128("1.5")]}], True],
            "arr": [0, [[MinKey(), {"a": [Decimal128("1.5")]}], True], "x"],
        },
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find deeply nested mixed BSON",
    ),
    ExpressionTestCase(
        "nested_inner_not_outer",
        doc={"val": [2, 3], "arr": [[1, [2, 3]], [2, 3], 4]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find inner array match",
    ),
    ExpressionTestCase(
        "nested_5_levels",
        doc={"val": [[[[99]]]], "arr": [[[[[99]]]], "other"]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find 5-level nested array",
    ),
    ExpressionTestCase(
        "nested_deep_not_found",
        doc={"val": [2, 3], "arr": [[1, [2, 3]], [4, 5]]},
        expression={"$in": ["$val", "$arr"]},
        expected=False,
        msg="$in should not find array at wrong nesting level",
    ),
]

# Aggregate and test
# Property [Literal Evaluation]: $in nested array matching works with inline literal values.
TEST_SUBSET_FOR_LITERAL: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal_nested_find_object_in_mixed",
        doc=None,
        expression={"$in": [{"a": 1}, {"$literal": [1, "two", {"a": 1}, [3, 4], True]}]},
        expected=True,
        msg="$in should find object in literal nested mixed array",
    ),
    ExpressionTestCase(
        "literal_nested_3_levels",
        doc=None,
        expression={
            "$in": [{"$literal": [[2, 3], [4, 5]]}, {"$literal": [1, [[2, 3], [4, 5]], "end"]}]
        },
        expected=True,
        msg="$in should find 3-level nested array in literal",
    ),
    ExpressionTestCase(
        "literal_nested_deep_not_found",
        doc=None,
        expression={"$in": [{"$literal": [2, 3]}, {"$literal": [[1, [2, 3]], [4, 5]]}]},
        expected=False,
        msg="$in should not find array at wrong nesting level in literal",
    ),
]

ALL_TESTS = NESTED_MIXED_ARRAY_TESTS + DEEPLY_NESTED_TESTS + TEST_SUBSET_FOR_LITERAL


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_in_nested_insert(collection, test):
    """Test $in nested array matching with values from inserted documents."""
    if test.doc is None:
        result = execute_expression(collection, test.expression)
    else:
        result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
