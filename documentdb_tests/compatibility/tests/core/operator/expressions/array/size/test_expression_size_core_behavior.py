"""
Core behavior tests for $size expression.

Tests array length counting for various array types and sizes.
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
from documentdb_tests.framework.lazy_payload import lazy
from documentdb_tests.framework.parametrize import pytest_params

# Property [Element Count]: $size returns the number of top-level elements in an array.
BASIC_SIZE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "empty_array",
        expression={"$size": "$arr"},
        doc={"arr": []},
        expected=0,
        msg="$size should return 0 for an empty array",
    ),
    ExpressionTestCase(
        "single_element",
        expression={"$size": "$arr"},
        doc={"arr": [1]},
        expected=1,
        msg="$size should return 1 for a single-element array",
    ),
    ExpressionTestCase(
        "single_null_element",
        expression={"$size": "$arr"},
        doc={"arr": [None]},
        expected=1,
        msg="$size should return 1 for a single null element",
    ),
    ExpressionTestCase(
        "three_elements",
        expression={"$size": "$arr"},
        doc={"arr": [1, 2, 3]},
        expected=3,
        msg="$size should return 3 for a three-element array",
    ),
    ExpressionTestCase(
        "five_elements",
        expression={"$size": "$arr"},
        doc={"arr": [1, 2, 3, 4, 5]},
        expected=5,
        msg="$size should return 5 for a five-element array",
    ),
    ExpressionTestCase(
        "all_same",
        expression={"$size": "$arr"},
        doc={"arr": [1, 1, 1, 1]},
        expected=4,
        msg="$size should count duplicate elements",
    ),
    ExpressionTestCase(
        "string_array",
        expression={"$size": "$arr"},
        doc={"arr": ["a", "b", "c"]},
        expected=3,
        msg="$size should count string elements",
    ),
]

# Property [Element Type Independence]: $size counts every element regardless of type.
ELEMENT_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "mixed_types",
        expression={"$size": "$arr"},
        doc={"arr": [1, "two", True, None, {"a": 1}, [1, 2]]},
        expected=6,
        msg="$size should count mixed-type elements",
    ),
    ExpressionTestCase(
        "nested_arrays",
        expression={"$size": "$arr"},
        doc={"arr": [[1, 2], [3, 4], [5, 6]]},
        expected=3,
        msg="$size should count top-level elements without flattening",
    ),
    ExpressionTestCase(
        "array_of_objects",
        expression={"$size": "$arr"},
        doc={"arr": [{"a": 1}, {"b": 2}]},
        expected=2,
        msg="$size should count object elements",
    ),
    ExpressionTestCase(
        "array_of_nulls",
        expression={"$size": "$arr"},
        doc={"arr": [None, None, None]},
        expected=3,
        msg="$size should count null elements",
    ),
    ExpressionTestCase(
        "array_with_empty_subarrays",
        expression={"$size": "$arr"},
        doc={"arr": [[], [], []]},
        expected=3,
        msg="$size should count empty subarray elements",
    ),
    ExpressionTestCase(
        "empty_object_element",
        expression={"$size": "$arr"},
        doc={"arr": [{}]},
        expected=1,
        msg="$size should count an empty object element",
    ),
    ExpressionTestCase(
        "empty_string_element",
        expression={"$size": "$arr"},
        doc={"arr": [""]},
        expected=1,
        msg="$size should count an empty string element",
    ),
    ExpressionTestCase(
        "zero_element",
        expression={"$size": "$arr"},
        doc={"arr": [0]},
        expected=1,
        msg="$size should count a zero element",
    ),
    ExpressionTestCase(
        "false_element",
        expression={"$size": "$arr"},
        doc={"arr": [False]},
        expected=1,
        msg="$size should count a false element",
    ),
    ExpressionTestCase(
        "single_nested_array",
        expression={"$size": "$arr"},
        doc={"arr": [[1, 2, 3]]},
        expected=1,
        msg="$size should count a single nested array as one element",
    ),
]

# Property [Large Arrays]: $size returns the correct count for large arrays.
LARGE_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "large_array",
        expression={"$size": "$arr"},
        doc=lazy(lambda: {"arr": list(range(10_000))}),
        expected=10_000,
        msg="$size should count a large array's elements",
    ),
    ExpressionTestCase(
        "large_string_element",
        expression={"$size": "$arr"},
        doc=lazy(lambda: {"arr": ["x" * 1_000_000]}),
        expected=1,
        msg="$size should count a single large string element as one element",
    ),
]

ALL_TESTS = BASIC_SIZE_TESTS + ELEMENT_TYPE_TESTS + LARGE_ARRAY_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_size_insert(collection, test):
    """Test $size with values from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


# Property [Literal Input]: $size counts an array passed as a literal.
SIZE_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal_empty",
        expression={"$size": {"$literal": []}},
        expected=0,
        msg="$size should count a literal empty array",
    ),
    ExpressionTestCase(
        "literal_three_elements",
        expression={"$size": {"$literal": [1, 2, 3]}},
        expected=3,
        msg="$size should count a literal array's elements",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SIZE_LITERAL_TESTS))
def test_size_literal(collection, test):
    """Test $size with literal values."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
