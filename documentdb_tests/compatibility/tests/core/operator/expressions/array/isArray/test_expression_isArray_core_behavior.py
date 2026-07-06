"""
Core behavior tests for $isArray expression.

Tests that arrays return true, non-arrays return false,
with basic types via both literal and insert paths.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.array.utils.array_test_case import (  # noqa: E501
    ArrayTestClass,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Success: arrays → true
IS_ARRAY_TRUE_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="simple_array",
        value=[1, 2, 3],
        expected=True,
        msg="Should return true for simple array",
    ),
    ArrayTestClass(
        id="empty_array",
        value=[],
        expected=True,
        msg="Should return true for empty array",
    ),
    ArrayTestClass(
        id="single_element",
        value=[42],
        expected=True,
        msg="Should return true for single-element array",
    ),
    ArrayTestClass(
        id="nested_array",
        value=[[1, 2], [3, 4]],
        expected=True,
        msg="Should return true for nested array",
    ),
    ArrayTestClass(
        id="mixed_type_array",
        value=[1, "two", True, None, {"a": 1}],
        expected=True,
        msg="Should return true for mixed-type array",
    ),
    ArrayTestClass(
        id="array_of_objects",
        value=[{"a": 1}, {"b": 2}],
        expected=True,
        msg="Should return true for array of objects",
    ),
    ArrayTestClass(
        id="array_of_nulls",
        value=[None, None],
        expected=True,
        msg="Should return true for array of nulls",
    ),
    ArrayTestClass(
        id="string_array",
        value=["a", "b", "c"],
        expected=True,
        msg="Should return true for string array",
    ),
    ArrayTestClass(
        id="bool_array",
        value=[True],
        expected=True,
        msg="Should return true for bool array",
    ),
    ArrayTestClass(
        id="large_array_10k",
        value=list(range(10000)),
        expected=True,
        msg="10K element array returns true",
    ),
    ArrayTestClass(
        id="deeply_nested_array",
        value=[[[[[[1]]]]]],
        expected=True,
        msg="Deeply nested array returns true",
    ),
    ArrayTestClass(
        id="large_array_of_arrays",
        value=[[i] for i in range(10000)],
        expected=True,
        msg="10K nested arrays returns true",
    ),
]

# Success: non-arrays → false
IS_ARRAY_FALSE_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="string", value="hello", expected=False, msg="Should return false for string"
    ),
    ArrayTestClass(id="int", value=42, expected=False, msg="Should return false for int"),
    ArrayTestClass(id="double", value=3.14, expected=False, msg="Should return false for double"),
    ArrayTestClass(id="bool_true", value=True, expected=False, msg="Should return false for true"),
    ArrayTestClass(
        id="bool_false", value=False, expected=False, msg="Should return false for false"
    ),
    ArrayTestClass(id="null", value=None, expected=False, msg="Should return false for null"),
    ArrayTestClass(
        id="object", value={"a": 1}, expected=False, msg="Should return false for object"
    ),
    ArrayTestClass(
        id="empty_string", value="", expected=False, msg="Should return false for empty string"
    ),
    ArrayTestClass(
        id="empty_object", value={}, expected=False, msg="Should return false for empty object"
    ),
    ArrayTestClass(id="zero", value=0, expected=False, msg="Should return false for zero"),
    ArrayTestClass(
        id="negative_int", value=-123, expected=False, msg="Should return false for negative int"
    ),
    ArrayTestClass(
        id="negative_double",
        value=-1.23,
        expected=False,
        msg="Should return false for negative double",
    ),
]

# Array-like edge cases → false
ARRAY_LIKE_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="string_brackets", value="[]", expected=False, msg="Should return false for string '[]'"
    ),
    ArrayTestClass(
        id="string_array_repr",
        value="[1, 2, 3]",
        expected=False,
        msg="Should return false for string '[1, 2, 3]'",
    ),
    ArrayTestClass(
        id="array_like_object",
        value={"0": "a", "1": "b"},
        expected=False,
        msg="Should return false for array-like object",
    ),
    ArrayTestClass(
        id="length_object",
        value={"length": 3},
        expected=False,
        msg="Should return false for object with length key",
    ),
]

# Aggregate and test
INSERT_TESTS = IS_ARRAY_TRUE_TESTS + IS_ARRAY_FALSE_TESTS + ARRAY_LIKE_TESTS


@pytest.mark.parametrize("test", pytest_params(INSERT_TESTS))
def test_isArray_insert(collection, test):
    """Test $isArray with values from inserted documents."""
    result = execute_expression_with_insert(collection, {"$isArray": "$val"}, {"val": test.value})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


TEST_SUBSET_FOR_LITERAL = [
    IS_ARRAY_TRUE_TESTS[0],  # simple_array
    IS_ARRAY_TRUE_TESTS[1],  # empty_array
    IS_ARRAY_TRUE_TESTS[3],  # nested_array
    IS_ARRAY_TRUE_TESTS[5],  # array_of_objects
    IS_ARRAY_TRUE_TESTS[6],  # array_of_nulls
    IS_ARRAY_FALSE_TESTS[0],  # string
    IS_ARRAY_FALSE_TESTS[1],  # int
    IS_ARRAY_FALSE_TESTS[3],  # bool_true
    IS_ARRAY_FALSE_TESTS[4],  # bool_false
    IS_ARRAY_FALSE_TESTS[5],  # null
    IS_ARRAY_FALSE_TESTS[6],  # object
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_isArray_literal(collection, test):
    """Test $isArray with literal values."""
    expr = {"$literal": test.value} if isinstance(test.value, list) else test.value
    result = execute_expression(collection, {"$isArray": [expr]})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
