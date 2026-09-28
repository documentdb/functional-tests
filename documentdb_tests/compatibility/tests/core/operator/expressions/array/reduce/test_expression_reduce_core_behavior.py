"""
Core behavior tests for $reduce expression.

Tests basic reduction (sum, product, concat), empty arrays, null propagation,
various initialValue types, nested arrays, objects as elements, and large arrays.
"""

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Basic Reduction]: $reduce folds the array left to right applying 'in'.
BASIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "basic_sum",
        expression={
            "$reduce": {"input": "$arr", "initialValue": 0, "in": {"$add": ["$$value", "$$this"]}}
        },
        doc={"arr": [1, 2, 3, 4, 5]},
        expected=15,
        msg="$reduce should sum all elements",
    ),
    ExpressionTestCase(
        "basic_product",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": 1,
                "in": {"$multiply": ["$$value", "$$this"]},
            }
        },
        doc={"arr": [1, 2, 3, 4]},
        expected=24,
        msg="$reduce should multiply all elements",
    ),
    ExpressionTestCase(
        "basic_string_concat",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": "",
                "in": {"$concat": ["$$value", "$$this"]},
            }
        },
        doc={"arr": ["a", "b", "c"]},
        expected="abc",
        msg="$reduce should concatenate strings",
    ),
    ExpressionTestCase(
        "basic_count_elements",
        expression={
            "$reduce": {"input": "$arr", "initialValue": 0, "in": {"$add": ["$$value", 1]}}
        },
        doc={"arr": ["a", "b", "c", "d"]},
        expected=4,
        msg="$reduce should count elements",
    ),
]

# Property [Empty Input]: an empty input array returns initialValue unchanged.
EMPTY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "empty_array_int_init",
        expression={
            "$reduce": {"input": "$arr", "initialValue": 0, "in": {"$add": ["$$value", "$$this"]}}
        },
        doc={"arr": []},
        expected=0,
        msg="$reduce should return initialValue for an empty array",
    ),
    ExpressionTestCase(
        "empty_array_string_init",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": "start",
                "in": {"$concat": ["$$value", "$$this"]},
            }
        },
        doc={"arr": []},
        expected="start",
        msg="$reduce should return the string initialValue for an empty array",
    ),
    ExpressionTestCase(
        "empty_array_array_init",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": [],
                "in": {"$concatArrays": ["$$value", ["$$this"]]},
            }
        },
        doc={"arr": []},
        expected=[],
        msg="$reduce should return the array initialValue for an empty array",
    ),
    ExpressionTestCase(
        "empty_array_object_init",
        expression={"$reduce": {"input": "$arr", "initialValue": {"count": 0}, "in": "$$value"}},
        doc={"arr": []},
        expected={"count": 0},
        msg="$reduce should return the object initialValue for an empty array",
    ),
    ExpressionTestCase(
        "empty_array_null_init",
        expression={"$reduce": {"input": "$arr", "initialValue": None, "in": "$$value"}},
        doc={"arr": []},
        expected=None,
        msg="$reduce should return the null initialValue for an empty array",
    ),
    ExpressionTestCase(
        "empty_array_bool_init",
        expression={"$reduce": {"input": "$arr", "initialValue": True, "in": "$$value"}},
        doc={"arr": []},
        expected=True,
        msg="$reduce should return the true initialValue for an empty array",
    ),
    ExpressionTestCase(
        "empty_array_bool_false_init",
        expression={"$reduce": {"input": "$arr", "initialValue": False, "in": "$$value"}},
        doc={"arr": []},
        expected=False,
        msg="$reduce should return the false initialValue for an empty array",
    ),
]

# Property [Null Input]: a null input array returns null.
NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_input",
        expression={
            "$reduce": {"input": "$arr", "initialValue": 0, "in": {"$add": ["$$value", "$$this"]}}
        },
        doc={"arr": None},
        expected=None,
        msg="$reduce should return null when input is null",
    ),
]

# Property [Single Element]: a one-element array applies 'in' exactly once.
SINGLE_ELEMENT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "single_element_sum",
        expression={
            "$reduce": {"input": "$arr", "initialValue": 0, "in": {"$add": ["$$value", "$$this"]}}
        },
        doc={"arr": [42]},
        expected=42,
        msg="$reduce should reduce a single element",
    ),
    ExpressionTestCase(
        "single_element_identity",
        expression={"$reduce": {"input": "$arr", "initialValue": 0, "in": "$$this"}},
        doc={"arr": [99]},
        expected=99,
        msg="$reduce should return the element for a single-element identity reduction",
    ),
]

# Property [Array Accumulator]: $concatArrays in 'in' flattens nested arrays.
NESTED_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "flatten_one_level",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": [],
                "in": {"$concatArrays": ["$$value", "$$this"]},
            }
        },
        doc={"arr": [[1, 2], [3, 4], [5]]},
        expected=[1, 2, 3, 4, 5],
        msg="$reduce should flatten one level of nesting",
    ),
    ExpressionTestCase(
        "flatten_with_empty",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": [],
                "in": {"$concatArrays": ["$$value", "$$this"]},
            }
        },
        doc={"arr": [[1], [], [2, 3], []]},
        expected=[1, 2, 3],
        msg="$reduce should flatten with empty subarrays",
    ),
]

# Property [Object Elements]: 'in' can read fields of object elements.
OBJECT_ELEMENT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "sum_object_field",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": 0,
                "in": {"$add": ["$$value", "$$this.val"]},
            }
        },
        doc={"arr": [{"val": 10}, {"val": 20}, {"val": 30}]},
        expected=60,
        msg="$reduce should sum object field values",
    ),
    ExpressionTestCase(
        "merge_objects",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": {},
                "in": {"$mergeObjects": ["$$value", "$$this"]},
            }
        },
        doc={"arr": [{"a": 1}, {"b": 2}, {"c": 3}]},
        expected={"a": 1, "b": 2, "c": 3},
        msg="$reduce should merge objects",
    ),
]

# Property [Array Building]: 'in' can grow the accumulator array.
ACCUMULATE_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "collect_into_array",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": [],
                "in": {"$concatArrays": ["$$value", ["$$this"]]},
            }
        },
        doc={"arr": [1, 2, 3]},
        expected=[1, 2, 3],
        msg="$reduce should collect elements into an array",
    ),
    ExpressionTestCase(
        "collect_doubled",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": [],
                "in": {"$concatArrays": ["$$value", [{"$multiply": ["$$this", 2]}]]},
            }
        },
        doc={"arr": [1, 2, 3]},
        expected=[2, 4, 6],
        msg="$reduce should collect doubled elements",
    ),
]

# Property [Boolean Reduction]: boolean 'in' operators fold to a single boolean.
BOOLEAN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "all_true",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": True,
                "in": {"$and": ["$$value", "$$this"]},
            }
        },
        doc={"arr": [True, True, True]},
        expected=True,
        msg="$reduce should reduce all-true to true",
    ),
    ExpressionTestCase(
        "and_short_circuits_on_false",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": True,
                "in": {"$and": ["$$value", "$$this"]},
            }
        },
        doc={"arr": [True, False, True]},
        expected=False,
        msg="$reduce should reduce to false when any element is false",
    ),
    ExpressionTestCase(
        "any_true",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": False,
                "in": {"$or": ["$$value", "$$this"]},
            }
        },
        doc={"arr": [False, False, True]},
        expected=True,
        msg="$reduce should reduce to true when any element is true via $or",
    ),
]

# Property [Large Input]: reduction handles large arrays.
LARGE_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "large_array_sum",
        expression={
            "$reduce": {"input": "$arr", "initialValue": 0, "in": {"$add": ["$$value", "$$this"]}}
        },
        doc={"arr": list(range(10_000))},
        expected=sum(range(10_000)),
        msg="$reduce should sum a large array",
    ),
]

# Property [Evaluation Order]: elements are processed strictly left to right.
LEFT_TO_RIGHT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "concat_order",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": "",
                "in": {"$concat": ["$$value", "$$this"]},
            }
        },
        doc={"arr": ["a", "b", "c"]},
        expected="abc",
        msg="$reduce should apply 'in' left to right (right-to-left would yield 'cba')",
    ),
    ExpressionTestCase(
        "sequential_subtract",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": 100,
                "in": {"$subtract": ["$$value", "$$this"]},
            }
        },
        doc={"arr": [10, 5]},
        expected=85,
        msg="$reduce should apply $subtract once per element, accumulating the result",
    ),
    ExpressionTestCase(
        "sequential_divide",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": 100,
                "in": {"$divide": ["$$value", "$$this"]},
            }
        },
        doc={"arr": [2, 5]},
        expected=10.0,
        msg="$reduce should apply $divide once per element, accumulating the result",
    ),
]

# Property [Object Accumulator]: $$value can be an object carrying multiple sub-accumulators.
OBJECT_ACCUMULATOR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "sum_and_product",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": {"sum": 5, "product": 2},
                "in": {
                    "sum": {"$add": ["$$value.sum", "$$this"]},
                    "product": {"$multiply": ["$$value.product", "$$this"]},
                },
            }
        },
        doc={"arr": [1, 2, 3, 4]},
        expected={"sum": 15, "product": 48},
        msg="$reduce should support an object accumulator",
    ),
    ExpressionTestCase(
        "items_and_sum",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": {"items": [], "sum": 0},
                "in": {
                    "items": {"$concatArrays": ["$$value.items", ["$$this"]]},
                    "sum": {"$add": ["$$value.sum", "$$this"]},
                },
            }
        },
        doc={"arr": [1, 2, 3]},
        expected={"items": [1, 2, 3], "sum": 6},
        msg="$reduce should support an object accumulator with an array field",
    ),
]

# Property [In Expression]: 'in' accepts literals and $$value/$$this references.
IN_EXPR_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal_in",
        expression={"$reduce": {"input": "$arr", "initialValue": 0, "in": 42}},
        doc={"arr": [1, 2, 3]},
        expected=42,
        msg="$reduce should return the literal 'in' value each iteration",
    ),
    ExpressionTestCase(
        "value_ref_only",
        expression={"$reduce": {"input": "$arr", "initialValue": 0, "in": "$$value"}},
        doc={"arr": [1, 2, 3]},
        expected=0,
        msg="$reduce should return initialValue unchanged for a $$value-only 'in'",
    ),
    ExpressionTestCase(
        "this_ref_only",
        expression={"$reduce": {"input": "$arr", "initialValue": 0, "in": "$$this"}},
        doc={"arr": [10, 20, 30]},
        expected=30,
        msg="$reduce should return the last element for a $$this-only 'in'",
    ),
    ExpressionTestCase(
        "without_value",
        expression={"$reduce": {"input": "$arr", "initialValue": 5, "in": {"$add": [5, "$$this"]}}},
        doc={"arr": [1, 2, 3, 4]},
        expected=9,
        msg="$reduce should return the last evaluation when 'in' omits $$value",
    ),
    ExpressionTestCase(
        "without_this",
        expression={
            "$reduce": {"input": "$arr", "initialValue": 5, "in": {"$add": ["$$value", 5]}}
        },
        doc={"arr": [1, 2, 3, 4]},
        expected=25,
        msg="$reduce should apply 'in' each iteration when it omits $$this",
    ),
]

# Property [Null Propagation]: a null element or null accumulator propagates through arithmetic.
NULL_PROPAGATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_propagates_add",
        expression={
            "$reduce": {"input": "$arr", "initialValue": 0, "in": {"$add": ["$$value", "$$this"]}}
        },
        doc={"arr": [1, None, 3]},
        expected=None,
        msg="$reduce should propagate a null element through $add",
    ),
    ExpressionTestCase(
        "null_with_ifNull",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": 0,
                "in": {"$add": ["$$value", {"$ifNull": ["$$this", 0]}]},
            }
        },
        doc={"arr": [1, None, 3]},
        expected=4,
        msg="$reduce should replace null with $ifNull before summing",
    ),
    ExpressionTestCase(
        "null_init_add",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": None,
                "in": {"$add": ["$$value", "$$this"]},
            }
        },
        doc={"arr": [1, 2]},
        expected=None,
        msg="$reduce should return null for a null initialValue with $add",
    ),
]

# Property [Heterogeneous Elements]: mixed element types are handled per the 'in' expression.
HETEROGENEOUS_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "collect_heterogeneous",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": [],
                "in": {"$concatArrays": ["$$value", ["$$this"]]},
            }
        },
        doc={"arr": [1, "two", True, None, [3], {"four": 4}]},
        expected=[1, "two", True, None, [3], {"four": 4}],
        msg="$reduce should collect all element types into an array",
    ),
    ExpressionTestCase(
        "type_bridge_tostring",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": "",
                "in": {"$concat": ["$$value", {"$toString": "$$this"}]},
            }
        },
        doc={"arr": [1, 2]},
        expected="12",
        msg="$reduce should bridge types via $toString",
    ),
    ExpressionTestCase(
        "int_init_decimal_elements",
        expression={
            "$reduce": {"input": "$arr", "initialValue": 0, "in": {"$add": ["$$value", "$$this"]}}
        },
        doc={"arr": [Decimal128("1"), Decimal128("2")]},
        expected=Decimal128("3"),
        msg="$reduce should promote int initialValue with Decimal128 elements",
    ),
]

ALL_TESTS = (
    BASIC_TESTS
    + EMPTY_TESTS
    + NULL_TESTS
    + SINGLE_ELEMENT_TESTS
    + NESTED_ARRAY_TESTS
    + OBJECT_ELEMENT_TESTS
    + ACCUMULATE_ARRAY_TESTS
    + BOOLEAN_TESTS
    + LARGE_ARRAY_TESTS
    + LEFT_TO_RIGHT_TESTS
    + OBJECT_ACCUMULATOR_TESTS
    + IN_EXPR_TYPE_TESTS
    + NULL_PROPAGATION_TESTS
    + HETEROGENEOUS_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_reduce_insert(collection, test):
    """Test $reduce with values from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
