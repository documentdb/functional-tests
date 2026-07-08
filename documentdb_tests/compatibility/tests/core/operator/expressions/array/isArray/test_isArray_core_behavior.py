"""
Core behavior tests for $isArray expression.

Tests that arrays return true, non-arrays return false,
with basic types.
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

# Success: arrays → true
IS_ARRAY_TRUE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "simple_array",
        doc={"val": [1, 2, 3]},
        expression={"$isArray": "$val"},
        expected=True,
        msg="$isArray should return true for simple array",
    ),
    ExpressionTestCase(
        "empty_array",
        doc={"val": []},
        expression={"$isArray": "$val"},
        expected=True,
        msg="$isArray should return true for empty array",
    ),
    ExpressionTestCase(
        "single_element",
        doc={"val": [42]},
        expression={"$isArray": "$val"},
        expected=True,
        msg="$isArray should return true for single-element array",
    ),
    ExpressionTestCase(
        "nested_array",
        doc={"val": [[1, 2], [3, 4]]},
        expression={"$isArray": "$val"},
        expected=True,
        msg="$isArray should return true for nested array",
    ),
    ExpressionTestCase(
        "mixed_type_array",
        doc={"val": [1, "two", True, None, {"a": 1}]},
        expression={"$isArray": "$val"},
        expected=True,
        msg="$isArray should return true for mixed-type array",
    ),
    ExpressionTestCase(
        "array_of_objects",
        doc={"val": [{"a": 1}, {"b": 2}]},
        expression={"$isArray": "$val"},
        expected=True,
        msg="$isArray should return true for array of objects",
    ),
    ExpressionTestCase(
        "array_of_nulls",
        doc={"val": [None, None]},
        expression={"$isArray": "$val"},
        expected=True,
        msg="$isArray should return true for array of nulls",
    ),
    ExpressionTestCase(
        "string_array",
        doc={"val": ["a", "b", "c"]},
        expression={"$isArray": "$val"},
        expected=True,
        msg="$isArray should return true for string array",
    ),
    ExpressionTestCase(
        "bool_array",
        doc={"val": [True]},
        expression={"$isArray": "$val"},
        expected=True,
        msg="$isArray should return true for bool array",
    ),
    ExpressionTestCase(
        "large_array_10k",
        doc={"val": list(range(10000))},
        expression={"$isArray": "$val"},
        expected=True,
        msg="$isArray 10K element array returns true",
    ),
    ExpressionTestCase(
        "deeply_nested_array",
        doc={"val": [[[[[[1]]]]]]},
        expression={"$isArray": "$val"},
        expected=True,
        msg="$isArray deeply nested array returns true",
    ),
    ExpressionTestCase(
        "large_array_of_arrays",
        doc={"val": [[i] for i in range(10000)]},
        expression={"$isArray": "$val"},
        expected=True,
        msg="$isArray 10K nested arrays returns true",
    ),
]

# Success: non-arrays → false
IS_ARRAY_FALSE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "string",
        doc={"val": "hello"},
        expression={"$isArray": "$val"},
        expected=False,
        msg="$isArray should return false for string",
    ),
    ExpressionTestCase(
        "int",
        doc={"val": 42},
        expression={"$isArray": "$val"},
        expected=False,
        msg="$isArray should return false for int",
    ),
    ExpressionTestCase(
        "double",
        doc={"val": 3.14},
        expression={"$isArray": "$val"},
        expected=False,
        msg="$isArray should return false for double",
    ),
    ExpressionTestCase(
        "bool_true",
        doc={"val": True},
        expression={"$isArray": "$val"},
        expected=False,
        msg="$isArray should return false for true",
    ),
    ExpressionTestCase(
        "bool_false",
        doc={"val": False},
        expression={"$isArray": "$val"},
        expected=False,
        msg="$isArray should return false for false",
    ),
    ExpressionTestCase(
        "null",
        doc={"val": None},
        expression={"$isArray": "$val"},
        expected=False,
        msg="$isArray should return false for null",
    ),
    ExpressionTestCase(
        "object",
        doc={"val": {"a": 1}},
        expression={"$isArray": "$val"},
        expected=False,
        msg="$isArray should return false for object",
    ),
    ExpressionTestCase(
        "empty_string",
        doc={"val": ""},
        expression={"$isArray": "$val"},
        expected=False,
        msg="$isArray should return false for empty string",
    ),
    ExpressionTestCase(
        "empty_object",
        doc={"val": {}},
        expression={"$isArray": "$val"},
        expected=False,
        msg="$isArray should return false for empty object",
    ),
    ExpressionTestCase(
        "zero",
        doc={"val": 0},
        expression={"$isArray": "$val"},
        expected=False,
        msg="$isArray should return false for zero",
    ),
    ExpressionTestCase(
        "negative_int",
        doc={"val": -123},
        expression={"$isArray": "$val"},
        expected=False,
        msg="$isArray should return false for negative int",
    ),
    ExpressionTestCase(
        "negative_double",
        doc={"val": -1.23},
        expression={"$isArray": "$val"},
        expected=False,
        msg="$isArray should return false for negative double",
    ),
]

# Array-like edge cases → false
ARRAY_LIKE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "string_brackets",
        doc={"val": "[]"},
        expression={"$isArray": "$val"},
        expected=False,
        msg="$isArray should return false for string '[]'",
    ),
    ExpressionTestCase(
        "string_array_repr",
        doc={"val": "[1, 2, 3]"},
        expression={"$isArray": "$val"},
        expected=False,
        msg="$isArray should return false for string '[1, 2, 3]'",
    ),
    ExpressionTestCase(
        "array_like_object",
        doc={"val": {"0": "a", "1": "b"}},
        expression={"$isArray": "$val"},
        expected=False,
        msg="$isArray should return false for array-like object",
    ),
    ExpressionTestCase(
        "length_object",
        doc={"val": {"length": 3}},
        expression={"$isArray": "$val"},
        expected=False,
        msg="$isArray should return false for object with length key",
    ),
]

# Aggregate and test
# Property [Literal Evaluation]: $isArray evaluates correctly with inline literal values.
TEST_SUBSET_FOR_LITERAL: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal_simple_array",
        doc=None,
        expression={"$isArray": [{"$literal": [1, 2, 3]}]},
        expected=True,
        msg="$isArray should return true for literal simple array",
    ),
    ExpressionTestCase(
        "literal_empty_array",
        doc=None,
        expression={"$isArray": [{"$literal": []}]},
        expected=True,
        msg="$isArray should return true for literal empty array",
    ),
    ExpressionTestCase(
        "literal_nested_array",
        doc=None,
        expression={"$isArray": [{"$literal": [[1], [2]]}]},
        expected=True,
        msg="$isArray should return true for literal nested array",
    ),
    ExpressionTestCase(
        "literal_array_of_objects",
        doc=None,
        expression={"$isArray": [{"$literal": [{"a": 1}, {"b": 2}]}]},
        expected=True,
        msg="$isArray should return true for literal array of objects",
    ),
    ExpressionTestCase(
        "literal_array_of_nulls",
        doc=None,
        expression={"$isArray": [{"$literal": [None, None]}]},
        expected=True,
        msg="$isArray should return true for literal array of nulls",
    ),
    ExpressionTestCase(
        "literal_string",
        doc=None,
        expression={"$isArray": ["hello"]},
        expected=False,
        msg="$isArray should return false for literal string",
    ),
    ExpressionTestCase(
        "literal_int",
        doc=None,
        expression={"$isArray": [42]},
        expected=False,
        msg="$isArray should return false for literal int",
    ),
    ExpressionTestCase(
        "literal_bool_true",
        doc=None,
        expression={"$isArray": [True]},
        expected=False,
        msg="$isArray should return false for literal true",
    ),
    ExpressionTestCase(
        "literal_bool_false",
        doc=None,
        expression={"$isArray": [False]},
        expected=False,
        msg="$isArray should return false for literal false",
    ),
    ExpressionTestCase(
        "literal_null",
        doc=None,
        expression={"$isArray": [None]},
        expected=False,
        msg="$isArray should return false for literal null",
    ),
    ExpressionTestCase(
        "literal_object",
        doc=None,
        expression={"$isArray": [{"$literal": {"a": 1}}]},
        expected=False,
        msg="$isArray should return false for literal object",
    ),
]

INSERT_TESTS = (
    IS_ARRAY_TRUE_TESTS + IS_ARRAY_FALSE_TESTS + ARRAY_LIKE_TESTS + TEST_SUBSET_FOR_LITERAL
)


@pytest.mark.parametrize("test", pytest_params(INSERT_TESTS))
def test_isArray_insert(collection, test):
    """Test $isArray with values from inserted documents."""
    if test.doc is None:
        result = execute_expression(collection, test.expression)
    else:
        result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
