"""
Core behavior tests for $in expression.

Tests value found/not found, mixed types, and large arrays.
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

# ---------------------------------------------------------------------------
# Success: value found in array → True
# ---------------------------------------------------------------------------
FOUND_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="found_int", value=2, array=[1, 2, 3], expected=True, msg="Should find int in array"
    ),
    ArrayTestClass(
        id="found_first", value=1, array=[1, 2, 3], expected=True, msg="Should find first element"
    ),
    ArrayTestClass(
        id="found_last", value=3, array=[1, 2, 3], expected=True, msg="Should find last element"
    ),
    ArrayTestClass(
        id="found_string",
        value="b",
        array=["a", "b", "c"],
        expected=True,
        msg="Should find string in array",
    ),
    ArrayTestClass(
        id="found_bool_true",
        value=True,
        array=[True, False],
        expected=True,
        msg="Should find true in array",
    ),
    ArrayTestClass(
        id="found_bool_false",
        value=False,
        array=[True, False],
        expected=True,
        msg="Should find false in array",
    ),
    ArrayTestClass(
        id="found_null",
        value=None,
        array=[None, 1, 2],
        expected=True,
        msg="Should find null in array",
    ),
    ArrayTestClass(
        id="found_nested_array",
        value=[3, 4],
        array=[[1, 2], [3, 4]],
        expected=True,
        msg="Should find nested array",
    ),
    ArrayTestClass(
        id="found_object",
        value={"a": 1},
        array=[{"a": 1}, {"b": 2}],
        expected=True,
        msg="Should find object in array",
    ),
    ArrayTestClass(
        id="found_single_element",
        value=42,
        array=[42],
        expected=True,
        msg="Should find value in single-element array",
    ),
    ArrayTestClass(
        id="found_duplicate",
        value=5,
        array=[5, 5, 5],
        expected=True,
        msg="Should find value in array of duplicates",
    ),
]

# ---------------------------------------------------------------------------
# Success: value not found → False
# ---------------------------------------------------------------------------
NOT_FOUND_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="not_found_int",
        value=4,
        array=[1, 2, 3],
        expected=False,
        msg="Should not find absent int",
    ),
    ArrayTestClass(
        id="not_found_string",
        value="z",
        array=["a", "b"],
        expected=False,
        msg="Should not find absent string",
    ),
    ArrayTestClass(
        id="not_found_empty_array",
        value=1,
        array=[],
        expected=False,
        msg="Should not find value in empty array",
    ),
    ArrayTestClass(
        id="not_found_type_mismatch",
        value="1",
        array=[1, 2, 3],
        expected=False,
        msg="Should not find string '1' in int array",
    ),
    ArrayTestClass(
        id="not_found_bool_vs_int",
        value=True,
        array=[1, 0],
        expected=False,
        msg="Should not find bool in int array",
    ),
    ArrayTestClass(
        id="not_found_null",
        value=None,
        array=[1, 2, 3],
        expected=False,
        msg="Should not find null in non-null array",
    ),
    ArrayTestClass(
        id="not_found_partial_array",
        value=[1],
        array=[[1, 2], [3, 4]],
        expected=False,
        msg="Should not find partial array match",
    ),
    ArrayTestClass(
        id="not_found_partial_object",
        value={"a": 1},
        array=[{"a": 1, "b": 2}],
        expected=False,
        msg="Should not find partial object match",
    ),
]

# ---------------------------------------------------------------------------
# Success: mixed types in array
# ---------------------------------------------------------------------------
MIXED_TYPE_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="mixed_find_string",
        value="2",
        array=[1, "2", True, None, [1]],
        expected=True,
        msg="Should find string in mixed-type array",
    ),
    ArrayTestClass(
        id="mixed_find_null",
        value=None,
        array=[1, "2", True, None, [1]],
        expected=True,
        msg="Should find null in mixed-type array",
    ),
    ArrayTestClass(
        id="mixed_find_array",
        value=[1],
        array=[1, "2", True, None, [1]],
        expected=True,
        msg="Should find array in mixed-type array",
    ),
    ArrayTestClass(
        id="mixed_not_found",
        value="x",
        array=[1, "2", True, None, [1]],
        expected=False,
        msg="Should not find absent value in mixed-type array",
    ),
]

# ---------------------------------------------------------------------------
# Success: large array
# ---------------------------------------------------------------------------
_LARGE_ARRAY_SIZE = 20_000
_LARGE_ARRAY = list(range(_LARGE_ARRAY_SIZE))

LARGE_ARRAY_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="large_array_found_first",
        value=0,
        array=_LARGE_ARRAY,
        expected=True,
        msg="Should find first element in large array",
    ),
    ArrayTestClass(
        id="large_array_found_last",
        value=_LARGE_ARRAY_SIZE - 1,
        array=_LARGE_ARRAY,
        expected=True,
        msg="Should find last element in large array",
    ),
    ArrayTestClass(
        id="large_array_found_middle",
        value=_LARGE_ARRAY_SIZE // 2,
        array=_LARGE_ARRAY,
        expected=True,
        msg="Should find middle element in large array",
    ),
    ArrayTestClass(
        id="large_array_not_found",
        value=-1,
        array=_LARGE_ARRAY,
        expected=False,
        msg="Should not find absent value in large array",
    ),
]

# ---------------------------------------------------------------------------
# Aggregate and test
# ---------------------------------------------------------------------------
ALL_TESTS = FOUND_TESTS + NOT_FOUND_TESTS + MIXED_TYPE_TESTS + LARGE_ARRAY_TESTS

TEST_SUBSET_FOR_LITERAL = [
    FOUND_TESTS[0],  # found_int
    NOT_FOUND_TESTS[0],  # not_found_int
    LARGE_ARRAY_TESTS[0],  # large_array_found_first
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_in_literal(collection, test):
    """Test $in with literal values."""
    result = execute_expression(collection, {"$in": [test.value, test.array]})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_in_insert(collection, test):
    """Test $in with values from inserted documents."""
    result = execute_expression_with_insert(
        collection, {"$in": ["$val", "$arr"]}, {"val": test.value, "arr": test.array}
    )
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
