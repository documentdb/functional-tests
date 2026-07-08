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

# Success: basic mapping
# Property [Basic Transform]: $map applies an expression to each element.
BASIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="multiply_each",
        expression={"$map": {"input": "$arr", "in": {"$multiply": ["$$this", 2]}}},
        doc={"arr": [1, 2, 3]},
        expected=[2, 4, 6],
        msg="Should multiply each element by 2",
    ),
    ExpressionTestCase(
        id="add_each",
        expression={"$map": {"input": "$arr", "in": {"$add": ["$$this", 5]}}},
        doc={"arr": [10, 20, 30]},
        expected=[15, 25, 35],
        msg="Should add 5 to each element",
    ),
    ExpressionTestCase(
        id="identity",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": [1, 2, 3]},
        expected=[1, 2, 3],
        msg="Identity transform should return same array",
    ),
    ExpressionTestCase(
        id="constant_in",
        expression={"$map": {"input": "$arr", "in": 13}},
        doc={"arr": [1, 2, 3]},
        expected=[13, 13, 13],
        msg="Constant in expression should repeat for each element",
    ),
    ExpressionTestCase(
        id="string_elements",
        expression={"$map": {"input": "$arr", "in": {"$toUpper": "$$this"}}},
        doc={"arr": ["a", "b", "c"]},
        expected=["A", "B", "C"],
        msg="Should uppercase each string element",
    ),
    ExpressionTestCase(
        id="bool_elements",
        expression={"$map": {"input": "$arr", "in": {"$not": "$$this"}}},
        doc={"arr": [True, False, True]},
        expected=[False, True, False],
        msg="Should negate each boolean element",
    ),
    ExpressionTestCase(
        id="single_element",
        expression={"$map": {"input": "$arr", "in": {"$add": ["$$this", 1]}}},
        doc={"arr": [42]},
        expected=[43],
        msg="Should map single element",
    ),
    ExpressionTestCase(
        id="empty_array",
        expression={"$map": {"input": "$arr", "in": {"$multiply": ["$$this", 2]}}},
        doc={"arr": []},
        expected=[],
        msg="Should return empty array for empty input",
    ),
    ExpressionTestCase(
        id="null_input",
        expression={"$map": {"input": "$arr", "in": {"$multiply": ["$$this", 2]}}},
        doc={"arr": None},
        expected=None,
        msg="Should return null when input is null",
    ),
    ExpressionTestCase(
        id="custom_as_var",
        expression={"$map": {"input": "$arr", "as": "val", "in": {"$multiply": ["$$val", 3]}}},
        doc={"arr": [1, 2, 3]},
        expected=[3, 6, 9],
        msg="Should use custom 'as' variable name",
    ),
]

# Success: nested arrays (map does not flatten)
# Property [Nested Arrays]: $map operates on nested array structures.
NESTED_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="nested_arrays_identity",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": [[1, 2], [3, 4]]},
        expected=[[1, 2], [3, 4]],
        msg="Should preserve nested arrays",
    ),
    ExpressionTestCase(
        id="nested_arrays_size",
        expression={"$map": {"input": "$arr", "in": {"$size": "$$this"}}},
        doc={"arr": [[1, 2], [3, 4, 5], []]},
        expected=[2, 3, 0],
        msg="Should compute size of each subarray",
    ),
    ExpressionTestCase(
        id="extract_field_from_objects",
        expression={"$map": {"input": "$arr", "in": "$$this.a"}},
        doc={"arr": [{"a": 1, "b": 2}, {"a": 3, "b": 4}]},
        expected=[1, 3],
        msg="Should extract field from each object element",
    ),
]

# Success: elements with null
NULL_ELEMENT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="null_elements_identity",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": [None, 1, None]},
        expected=[None, 1, None],
        msg="Should preserve null elements",
    ),
    ExpressionTestCase(
        id="null_elements_ifnull",
        expression={"$map": {"input": "$arr", "in": {"$ifNull": ["$$this", 0]}}},
        doc={"arr": [None, 1, None]},
        expected=[0, 1, 0],
        msg="Should replace null elements with $ifNull",
    ),
]

# Success: wrap each element
WRAP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="wrap_in_array",
        expression={"$map": {"input": "$arr", "in": ["$$this"]}},
        doc={"arr": [1, 2, 3]},
        expected=[[1], [2], [3]],
        msg="Should wrap each element in an array",
    ),
    ExpressionTestCase(
        id="wrap_in_object",
        expression={"$map": {"input": "$arr", "in": {"val": "$$this"}}},
        doc={"arr": [1, 2, 3]},
        expected=[{"val": 1}, {"val": 2}, {"val": 3}],
        msg="Should wrap each element in an object",
    ),
]

# Success: type conversion in expression
TYPE_CONVERSION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="to_string",
        expression={"$map": {"input": "$arr", "in": {"$toString": "$$this"}}},
        doc={"arr": [1, 2, 3]},
        expected=["1", "2", "3"],
        msg="Should convert each element to string",
    ),
    ExpressionTestCase(
        id="type_of_each",
        expression={"$map": {"input": "$arr", "in": {"$type": "$$this"}}},
        doc={"arr": [1, "two", True, None]},
        expected=["int", "string", "bool", "null"],
        msg="Should return type of each element",
    ),
]

# Success: large array
# Property [Large Arrays]: $map handles large arrays.
LARGE_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="large_array_1000",
        expression={"$map": {"input": "$arr", "in": {"$multiply": ["$$this", 2]}}},
        doc={"arr": list(range(1000))},
        expected=[i * 2 for i in range(1000)],
        msg="Should map over 1000 elements",
    ),
]

# Success: order preservation and duplicates
ORDER_DUPLICATE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="preserves_order",
        expression={"$map": {"input": "$arr", "in": {"$multiply": ["$$this", 10]}}},
        doc={"arr": [3, 1, 4, 1, 5, 9]},
        expected=[30, 10, 40, 10, 50, 90],
        msg="Should preserve element order",
    ),
    ExpressionTestCase(
        id="duplicate_elements",
        expression={"$map": {"input": "$arr", "in": {"$add": ["$$this", 10]}}},
        doc={"arr": [1, 1, 1, 1]},
        expected=[11, 11, 11, 11],
        msg="Should process all duplicate elements",
    ),
    ExpressionTestCase(
        id="duplicate_nulls",
        expression={"$map": {"input": "$arr", "in": {"$ifNull": ["$$this", 0]}}},
        doc={"arr": [None, None, None]},
        expected=[0, 0, 0],
        msg="Should process all null duplicates",
    ),
]


# Success: null element propagation
# Property [Null Propagation]: $map returns null when input is null.
NULL_PROPAGATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="null_add_propagation",
        expression={"$map": {"input": "$arr", "in": {"$add": ["$$this", 1]}}},
        doc={"arr": [None, None]},
        expected=[None, None],
        msg="Null + number should propagate null",
    ),
    ExpressionTestCase(
        id="null_in_mixed_add",
        expression={"$map": {"input": "$arr", "in": {"$add": ["$$this", 1]}}},
        doc={"arr": [1, 2, None, 4]},
        expected=[2, 3, None, 5],
        msg="Null element should propagate, others should add",
    ),
    ExpressionTestCase(
        id="null_input_ignores_in",
        expression={"$map": {"input": "$arr", "in": {"$add": [2, 1]}}},
        doc={"arr": None},
        expected=None,
        msg="Null input returns null regardless of in expression",
    ),
    ExpressionTestCase(
        id="null_element_in_ignores",
        expression={"$map": {"input": "$arr", "in": {"$add": [2, 1]}}},
        doc={"arr": [None]},
        expected=[3],
        msg="Expression ignoring element should still produce result",
    ),
]

# Success: conditional in expressions
CONDITIONAL_IN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="cond_classify",
        expression={
            "$map": {"input": "$arr", "in": {"$cond": [{"$gte": ["$$this", 3]}, "high", "low"]}}
        },
        doc={"arr": [1, 2, 3, 4]},
        expected=["low", "low", "high", "high"],
        msg="$cond should classify elements",
    ),
    ExpressionTestCase(
        id="cond_isarray",
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

# Success: complex nested in expressions
NESTED_IN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="nested_multiply_add",
        expression={"$map": {"input": "$arr", "in": {"$multiply": [{"$add": ["$$this", 1]}, 2]}}},
        doc={"arr": [1, 2, 3]},
        expected=[4, 6, 8],
        msg="Nested expression should work",
    ),
    ExpressionTestCase(
        id="self_reference_double",
        expression={"$map": {"input": "$arr", "in": {"$add": ["$$this", "$$this"]}}},
        doc={"arr": [1, 2, 3]},
        expected=[2, 4, 6],
        msg="Self-reference should double each element",
    ),
    ExpressionTestCase(
        id="produce_nested_arrays",
        expression={"$map": {"input": "$arr", "in": ["$$this", {"$multiply": ["$$this", 2]}]}},
        doc={"arr": [1, 2, 3]},
        expected=[[1, 2], [2, 4], [3, 6]],
        msg="Should produce nested arrays",
    ),
]

# Aggregate and test
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
