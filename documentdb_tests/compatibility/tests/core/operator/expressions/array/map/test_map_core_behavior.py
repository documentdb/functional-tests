"""
Core behavior tests for $map expression.

Tests basic mapping, identity transforms, nested arrays, null propagation,
empty arrays, various in expressions, default and custom 'as' variable,
and large arrays.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Basic Transform]: $map applies an expression to each array element.
# Property [Basic Transform]: $map applies an expression to each element.
BASIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "multiply_each",
        expression={"$map": {"input": "$arr", "in": {"$multiply": ["$$this", 2]}}},
        doc={"arr": [1, 2, 3]},
        expected=[2, 4, 6],
        msg="$map should multiply each element by 2",
    ),
    ExpressionTestCase(
        "add_each",
        expression={"$map": {"input": "$arr", "in": {"$add": ["$$this", 5]}}},
        doc={"arr": [10, 20, 30]},
        expected=[15, 25, 35],
        msg="$map should add 5 to each element",
    ),
    ExpressionTestCase(
        "identity",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": [1, 2, 3]},
        expected=[1, 2, 3],
        msg="$map identity transform should return same array",
    ),
    ExpressionTestCase(
        "constant_in",
        expression={"$map": {"input": "$arr", "in": 13}},
        doc={"arr": [1, 2, 3]},
        expected=[13, 13, 13],
        msg="$map constant in expression should repeat for each element",
    ),
    ExpressionTestCase(
        "string_elements",
        expression={"$map": {"input": "$arr", "in": {"$toUpper": "$$this"}}},
        doc={"arr": ["a", "b", "c"]},
        expected=["A", "B", "C"],
        msg="$map should uppercase each string element",
    ),
    ExpressionTestCase(
        "bool_elements",
        expression={"$map": {"input": "$arr", "in": {"$not": "$$this"}}},
        doc={"arr": [True, False, True]},
        expected=[False, True, False],
        msg="$map should negate each boolean element",
    ),
    ExpressionTestCase(
        "single_element",
        expression={"$map": {"input": "$arr", "in": {"$add": ["$$this", 1]}}},
        doc={"arr": [42]},
        expected=[43],
        msg="$map should map single element",
    ),
    ExpressionTestCase(
        "empty_array",
        expression={"$map": {"input": "$arr", "in": {"$multiply": ["$$this", 2]}}},
        doc={"arr": []},
        expected=[],
        msg="$map should return empty array for empty input",
    ),
    ExpressionTestCase(
        "null_input",
        expression={"$map": {"input": "$arr", "in": {"$multiply": ["$$this", 2]}}},
        doc={"arr": None},
        expected=None,
        msg="$map should return null when input is null",
    ),
    ExpressionTestCase(
        "custom_as_var",
        expression={"$map": {"input": "$arr", "as": "val", "in": {"$multiply": ["$$val", 3]}}},
        doc={"arr": [1, 2, 3]},
        expected=[3, 6, 9],
        msg="$map should use custom 'as' variable name",
    ),
]

# Property [Nested Arrays]: $map does not flatten nested array structures.
# Property [Nested Arrays]: $map operates on nested array structures.
NESTED_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_arrays_identity",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": [[1, 2], [3, 4]]},
        expected=[[1, 2], [3, 4]],
        msg="$map should preserve nested arrays",
    ),
    ExpressionTestCase(
        "nested_arrays_size",
        expression={"$map": {"input": "$arr", "in": {"$size": "$$this"}}},
        doc={"arr": [[1, 2], [3, 4, 5], []]},
        expected=[2, 3, 0],
        msg="$map should compute size of each subarray",
    ),
    ExpressionTestCase(
        "extract_field_from_objects",
        expression={"$map": {"input": "$arr", "in": "$$this.a"}},
        doc={"arr": [{"a": 1, "b": 2}, {"a": 3, "b": 4}]},
        expected=[1, 3],
        msg="$map should extract field from each object element",
    ),
]

# Property [Null Elements]: $map preserves null elements within the array.
NULL_ELEMENT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_elements_identity",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": [None, 1, None]},
        expected=[None, 1, None],
        msg="$map should preserve null elements",
    ),
    ExpressionTestCase(
        "null_elements_ifnull",
        expression={"$map": {"input": "$arr", "in": {"$ifNull": ["$$this", 0]}}},
        doc={"arr": [None, 1, None]},
        expected=[0, 1, 0],
        msg="$map should replace null elements with $ifNull",
    ),
]

# Property [Element Wrapping]: $map wraps each element in the specified structure.
WRAP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "wrap_in_array",
        expression={"$map": {"input": "$arr", "in": ["$$this"]}},
        doc={"arr": [1, 2, 3]},
        expected=[[1], [2], [3]],
        msg="$map should wrap each element in an array",
    ),
    ExpressionTestCase(
        "wrap_in_object",
        expression={"$map": {"input": "$arr", "in": {"val": "$$this"}}},
        doc={"arr": [1, 2, 3]},
        expected=[{"val": 1}, {"val": 2}, {"val": 3}],
        msg="$map should wrap each element in an object",
    ),
]

# Property [Type Conversion]: $map applies type conversion expressions to each element.
TYPE_CONVERSION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "to_string",
        expression={"$map": {"input": "$arr", "in": {"$toString": "$$this"}}},
        doc={"arr": [1, 2, 3]},
        expected=["1", "2", "3"],
        msg="$map should convert each element to string",
    ),
    ExpressionTestCase(
        "type_of_each",
        expression={"$map": {"input": "$arr", "in": {"$type": "$$this"}}},
        doc={"arr": [1, "two", True, None]},
        expected=["int", "string", "bool", "null"],
        msg="$map should return type of each element",
    ),
]

# Property [Large Arrays]: $map handles arrays with many elements.
# Property [Large Arrays]: $map handles large arrays.
LARGE_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "large_array_1000",
        expression={"$map": {"input": "$arr", "in": {"$multiply": ["$$this", 2]}}},
        doc={"arr": list(range(1000))},
        expected=[i * 2 for i in range(1000)],
        msg="$map should map over 1000 elements",
    ),
]

# Property [Order Preservation]: $map preserves element order and duplicates.
ORDER_DUPLICATE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "preserves_order",
        expression={"$map": {"input": "$arr", "in": {"$multiply": ["$$this", 10]}}},
        doc={"arr": [3, 1, 4, 1, 5, 9]},
        expected=[30, 10, 40, 10, 50, 90],
        msg="$map should preserve element order",
    ),
    ExpressionTestCase(
        "duplicate_elements",
        expression={"$map": {"input": "$arr", "in": {"$add": ["$$this", 10]}}},
        doc={"arr": [1, 1, 1, 1]},
        expected=[11, 11, 11, 11],
        msg="$map should process all duplicate elements",
    ),
    ExpressionTestCase(
        "duplicate_nulls",
        expression={"$map": {"input": "$arr", "in": {"$ifNull": ["$$this", 0]}}},
        doc={"arr": [None, None, None]},
        expected=[0, 0, 0],
        msg="$map should process all null duplicates",
    ),
]


# Property [Null Propagation]: $map returns null when input is null.
NULL_PROPAGATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_add_propagation",
        expression={"$map": {"input": "$arr", "in": {"$add": ["$$this", 1]}}},
        doc={"arr": [None, None]},
        expected=[None, None],
        msg="$map null + number should propagate null",
    ),
    ExpressionTestCase(
        "null_in_mixed_add",
        expression={"$map": {"input": "$arr", "in": {"$add": ["$$this", 1]}}},
        doc={"arr": [1, 2, None, 4]},
        expected=[2, 3, None, 5],
        msg="$map null element should propagate, others should add",
    ),
    ExpressionTestCase(
        "null_input_ignores_in",
        expression={"$map": {"input": "$arr", "in": {"$add": [2, 1]}}},
        doc={"arr": None},
        expected=None,
        msg="$map null input returns null regardless of in expression",
    ),
    ExpressionTestCase(
        "null_element_in_ignores",
        expression={"$map": {"input": "$arr", "in": {"$add": [2, 1]}}},
        doc={"arr": [None]},
        expected=[3],
        msg="$map expression ignoring element should still produce result",
    ),
]

# Property [Conditional Expressions]: $map supports conditional logic in the in expression.
CONDITIONAL_IN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "cond_classify",
        expression={
            "$map": {"input": "$arr", "in": {"$cond": [{"$gte": ["$$this", 3]}, "high", "low"]}}
        },
        doc={"arr": [1, 2, 3, 4]},
        expected=["low", "low", "high", "high"],
        msg="$cond should classify elements",
    ),
    ExpressionTestCase(
        "cond_isarray",
        expression={
            "$map": {
                "input": "$arr",
                "in": {"$cond": [{"$isArray": "$$this"}, {"$size": "$$this"}, -1]},
            }
        },
        doc={"arr": [[1, 2], "notArray", [3, 4, 5]]},
        expected=[2, -1, 3],
        msg="$cond with $isArray should work",
    ),
]

# Property [Nested Expressions]: $map supports deeply nested operator expressions.
NESTED_IN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_multiply_add",
        expression={"$map": {"input": "$arr", "in": {"$multiply": [{"$add": ["$$this", 1]}, 2]}}},
        doc={"arr": [1, 2, 3]},
        expected=[4, 6, 8],
        msg="$map nested expression should work",
    ),
    ExpressionTestCase(
        "self_reference_double",
        expression={"$map": {"input": "$arr", "in": {"$add": ["$$this", "$$this"]}}},
        doc={"arr": [1, 2, 3]},
        expected=[2, 4, 6],
        msg="$map self-reference should double each element",
    ),
    ExpressionTestCase(
        "produce_nested_arrays",
        expression={"$map": {"input": "$arr", "in": ["$$this", {"$multiply": ["$$this", 2]}]}},
        doc={"arr": [1, 2, 3]},
        expected=[[1, 2], [2, 4], [3, 6]],
        msg="$map should produce nested arrays",
    ),
]

ALL_TESTS = (
    BASIC_TESTS
    + NESTED_ARRAY_TESTS
    + NULL_ELEMENT_TESTS
    + WRAP_TESTS
    + TYPE_CONVERSION_TESTS
    + LARGE_ARRAY_TESTS
    + ORDER_DUPLICATE_TESTS
    + NULL_PROPAGATION_TESTS
    + CONDITIONAL_IN_TESTS
    + NESTED_IN_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_map_core_behavior(collection, test):
    """Test $map core behavior: transforms, null propagation, conditionals."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
