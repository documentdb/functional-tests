"""
Core behavior tests for $reverseArray expression.

Tests reversing arrays of various element types, empty arrays,
single elements, nested arrays (top-level only), duplicates,
large arrays, null input and null-element handling, and element/object
integrity preservation.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Literal-path parity]: representative cases from each group below
# also run through the literal-value path (not just via inserted documents).
# Defined here directly (not by positional index into the groups below) so
# the mapping is name-stable, and appended to ALL_TESTS below so they also
# get insert coverage.
TEST_SUBSET_FOR_LITERAL: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="ints",
        doc={"arr": [1, 2, 3]},
        expected=[3, 2, 1],
        msg="Should reverse int array",
    ),
    ExpressionTestCase(
        id="strings",
        doc={"arr": ["a", "b", "c"]},
        expected=["c", "b", "a"],
        msg="Should reverse string array",
    ),
    ExpressionTestCase(
        id="empty_array",
        doc={"arr": []},
        expected=[],
        msg="Should return empty array for empty input",
    ),
    ExpressionTestCase(
        id="nested_arrays",
        doc={"arr": [[1, 2, 3], [4, 5, 6]]},
        expected=[[4, 5, 6], [1, 2, 3]],
        msg="Should reverse top-level only, not subarrays",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_reverseArray_literal(collection, test):
    """Test $reverseArray with literal values."""
    result = execute_expression(collection, {"$reverseArray": {"$literal": test.doc["arr"]}})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


# Property [Basic reversal]: arrays of each common scalar/object element type
# (int, string, double, boolean, object, mixed numeric) are reversed in order,
# with each element's value and type preserved.
BASIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="doubles",
        doc={"arr": [1.1, 2.2, 3.3]},
        expected=[3.3, 2.2, 1.1],
        msg="Should reverse double array",
    ),
    ExpressionTestCase(
        id="booleans",
        doc={"arr": [True, True, False]},
        expected=[False, True, True],
        msg="Should reverse boolean array",
    ),
    ExpressionTestCase(
        id="objects",
        doc={"arr": [{"a": 1}, {"b": 2}, {"c": 3}]},
        expected=[{"c": 3}, {"b": 2}, {"a": 1}],
        msg="Should reverse array of objects",
    ),
    ExpressionTestCase(
        id="numeric_cross_types",
        doc={"arr": [1, Int64(2), 3.0, Decimal128("4")]},
        expected=[Decimal128("4"), 3.0, Int64(2), 1],
        msg="Should reverse mixed numeric types",
    ),
]

# Property [Degenerate lengths]: arrays of length 0, 1, and 2 are handled
# correctly by the reversal (no swap loop, no-op single element, single swap).
DEGENERATE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="single_element",
        doc={"arr": [42]},
        expected=[42],
        msg="Should return single element unchanged",
    ),
    ExpressionTestCase(
        id="two_elements",
        doc={"arr": [1, 2]},
        expected=[2, 1],
        msg="Should swap two elements",
    ),
]

# Property [Top-level only]: reversal only reorders the outer array; nested
# arrays and mixed nested elements keep their own element order untouched.
NESTED_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="nested_mixed",
        doc={"arr": [[1], "two", [3, 4]]},
        expected=[[3, 4], "two", [1]],
        msg="Should reverse top-level with mixed nested",
    ),
    ExpressionTestCase(
        id="deeply_nested",
        doc={"arr": [[[1, 2]], [[3, 4]]]},
        expected=[[[3, 4]], [[1, 2]]],
        msg="Should reverse top-level of deeply nested arrays",
    ),
]

# Property [Duplicate/palindrome invariance]: arrays with repeated values or
# palindromic symmetry are reversed by position, so their visible content is
# unchanged even though the underlying operation still ran.
DUPLICATE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="all_same",
        doc={"arr": [5, 5, 5]},
        expected=[5, 5, 5],
        msg="Should handle all identical values",
    ),
    ExpressionTestCase(
        id="palindrome",
        doc={"arr": [1, 2, 3, 2, 1]},
        expected=[1, 2, 3, 2, 1],
        msg="Palindrome array should be unchanged",
    ),
]

_LARGE = list(range(1000))

# Property [Scales to large arrays]: reversal correctness holds for an array
# large enough (1000 elements) to rule out small-input-only implementations.
LARGE_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="large_array",
        doc={"arr": _LARGE},
        expected=list(reversed(_LARGE)),
        msg="Should reverse large array",
    ),
]

# Property [Null propagation]: a null input returns null (rather than an
# error), and null elements inside an array are preserved like any other
# element through the reversal.
NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="null_input",
        doc={"arr": None},
        expected=None,
        msg="Should return null for null input",
    ),
    ExpressionTestCase(
        id="array_with_nulls",
        doc={"arr": [1, None, 3]},
        expected=[3, None, 1],
        msg="Null elements preserved",
    ),
    ExpressionTestCase(
        id="array_all_nulls",
        doc={"arr": [None, None]},
        expected=[None, None],
        msg="All null array reversed",
    ),
]

# Property [Element integrity]: reordering elements never mutates them —
# object field order/keys and embedded inner arrays inside each element are
# byte-for-byte identical to the original, just relocated.
ELEMENT_PRESERVATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="object_field_order",
        doc={"arr": [{"a": 1, "b": 2}, {"c": 3, "d": 4}]},
        expected=[{"c": 3, "d": 4}, {"a": 1, "b": 2}],
        msg="Object field order preserved",
    ),
    ExpressionTestCase(
        id="embedded_docs_with_arrays",
        doc={"arr": [{"items": [1, 2]}, {"items": [3, 4]}]},
        expected=[{"items": [3, 4]}, {"items": [1, 2]}],
        msg="Inner arrays in docs not reversed",
    ),
    ExpressionTestCase(
        id="array_of_objects",
        doc={"arr": [{"name": "a", "val": 1}, {"name": "b", "val": 2}, {"name": "c", "val": 3}]},
        expected=[{"name": "c", "val": 3}, {"name": "b", "val": 2}, {"name": "a", "val": 1}],
        msg="Object integrity preserved",
    ),
]

ALL_TESTS = (
    BASIC_TESTS
    + DEGENERATE_TESTS
    + NESTED_ARRAY_TESTS
    + DUPLICATE_TESTS
    + LARGE_ARRAY_TESTS
    + NULL_TESTS
    + ELEMENT_PRESERVATION_TESTS
    + TEST_SUBSET_FOR_LITERAL
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_reverseArray_insert(collection, test):
    """Test $reverseArray with values from inserted documents."""
    result = execute_expression_with_insert(collection, {"$reverseArray": "$arr"}, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
