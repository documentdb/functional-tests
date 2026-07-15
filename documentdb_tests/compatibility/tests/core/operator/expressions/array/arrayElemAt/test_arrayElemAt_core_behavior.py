"""
Core behavior tests for $arrayElemAt expression.

Tests basic positive/negative index access, duplicate values, and large arrays.
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

# Property [Positive Index]: $arrayElemAt returns the element at the given positive index.
POSITIVE_INDEX_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="first_element",
        doc={"arr": [1, 2, 3], "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=1,
        msg="$arrayElemAt should return first element",
    ),
    ExpressionTestCase(
        id="second_element",
        doc={"arr": [1, 2, 3], "idx": 1},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=2,
        msg="$arrayElemAt should return second element",
    ),
    ExpressionTestCase(
        id="last_element",
        doc={"arr": [1, 2, 3], "idx": 2},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=3,
        msg="$arrayElemAt should return last element",
    ),
    ExpressionTestCase(
        id="single_element_array",
        doc={"arr": [42], "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=42,
        msg="$arrayElemAt should return single element",
    ),
    ExpressionTestCase(
        id="string_elements",
        doc={"arr": ["a", "b", "c"], "idx": 1},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected="b",
        msg="$arrayElemAt should return string element",
    ),
    ExpressionTestCase(
        id="mixed_types",
        doc={"arr": [1, "two", 3.0, True], "idx": 2},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=3.0,
        msg="$arrayElemAt should return element from mixed-type array",
    ),
    ExpressionTestCase(
        id="nested_array_element",
        doc={"arr": [[1, 2], [3, 4]], "idx": 1},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=[3, 4],
        msg="$arrayElemAt should return nested array element",
    ),
    ExpressionTestCase(
        id="nested_object_element",
        doc={"arr": [{"a": 1}, {"b": 2}], "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected={"a": 1},
        msg="$arrayElemAt should return nested object element",
    ),
    ExpressionTestCase(
        id="null_element_in_array",
        doc={"arr": [None, 1, 2], "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=None,
        msg="$arrayElemAt should return null element",
    ),
    ExpressionTestCase(
        id="bool_element",
        doc={"arr": [True, False], "idx": 1},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=False,
        msg="$arrayElemAt should return bool element",
    ),
]

# Property [Negative Index]: $arrayElemAt counts from the end of the array for a negative index.
NEGATIVE_INDEX_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="last_via_neg1",
        doc={"arr": [1, 2, 3], "idx": -1},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=3,
        msg="$arrayElemAt should return last element via -1",
    ),
    ExpressionTestCase(
        id="second_to_last",
        doc={"arr": [1, 2, 3], "idx": -2},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=2,
        msg="$arrayElemAt should return second to last",
    ),
    ExpressionTestCase(
        id="first_via_neg_len",
        doc={"arr": [1, 2, 3], "idx": -3},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=1,
        msg="$arrayElemAt should return first via negative length",
    ),
    ExpressionTestCase(
        id="single_element_neg1",
        doc={"arr": [42], "idx": -1},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=42,
        msg="$arrayElemAt should return single element via -1",
    ),
]

# Property [Duplicate Values]: $arrayElemAt selects by position, ignoring duplicate elements.
DUPLICATE_VALUE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="dup_first",
        doc={"arr": [1, 1, 1], "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=1,
        msg="$arrayElemAt is unaffected by duplicate elements at index 0",
    ),
    ExpressionTestCase(
        id="dup_last",
        doc={"arr": [1, 1, 1], "idx": 2},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=1,
        msg="$arrayElemAt is unaffected by duplicate elements at the last index",
    ),
    ExpressionTestCase(
        id="dup_neg",
        doc={"arr": ["a", "a", "b", "a"], "idx": -1},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected="a",
        msg="$arrayElemAt is unaffected by duplicate elements at a negative index",
    ),
]

# Property [Large Array]: $arrayElemAt resolves positions within large arrays.
_LARGE_ARRAY_SIZE = 20_000
_LARGE_ARRAY = list(range(_LARGE_ARRAY_SIZE))

# Property [Large Arrays]: $concatArrays concatenates large arrays.
LARGE_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="large_array_first",
        doc={"arr": _LARGE_ARRAY, "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=0,
        msg="$arrayElemAt should return first in large array",
    ),
    ExpressionTestCase(
        id="large_array_last",
        doc={"arr": _LARGE_ARRAY, "idx": _LARGE_ARRAY_SIZE - 1},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=_LARGE_ARRAY_SIZE - 1,
        msg="$arrayElemAt should return last in large array",
    ),
    ExpressionTestCase(
        id="large_array_neg1",
        doc={"arr": _LARGE_ARRAY, "idx": -1},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=_LARGE_ARRAY_SIZE - 1,
        msg="$arrayElemAt should return last via -1 in large array",
    ),
    ExpressionTestCase(
        id="large_array_middle",
        doc={"arr": _LARGE_ARRAY, "idx": _LARGE_ARRAY_SIZE // 2},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=_LARGE_ARRAY_SIZE // 2,
        msg="$arrayElemAt should return middle in large array",
    ),
    ExpressionTestCase(
        id="large_array_neg_middle",
        doc={"arr": _LARGE_ARRAY, "idx": -(_LARGE_ARRAY_SIZE // 4)},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=_LARGE_ARRAY_SIZE - _LARGE_ARRAY_SIZE // 4,
        msg="$arrayElemAt should return negative middle in large array",
    ),
]

ALL_TESTS = POSITIVE_INDEX_TESTS + NEGATIVE_INDEX_TESTS + DUPLICATE_VALUE_TESTS + LARGE_ARRAY_TESTS

TEST_SUBSET_FOR_LITERAL: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "first_element_literal",
        doc=None,
        expression={"$arrayElemAt": [{"$literal": [1, 2, 3]}, 0]},
        expected=1,
        msg="$arrayElemAt should return first element from literal array",
    ),
    ExpressionTestCase(
        "last_via_neg1_literal",
        doc=None,
        expression={"$arrayElemAt": [{"$literal": [1, 2, 3]}, -1]},
        expected=3,
        msg="$arrayElemAt should return last element via -1 from literal array",
    ),
    ExpressionTestCase(
        "large_array_first_literal",
        doc=None,
        expression={"$arrayElemAt": [{"$literal": list(range(20_000))}, 0]},
        expected=0,
        msg="$arrayElemAt should return first element from large literal array",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_arrayElemAt_literal(collection, test):
    """Test $arrayElemAt with literal values."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_arrayElemAt_insert(collection, test):
    """Test $arrayElemAt with values from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
