from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.accumulator.first.utils.first_common import (  # noqa: E501
    FirstTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Core Element Extraction]: $first returns the first element of an
# array without flattening, and nested calls unwrap one layer per level.
FIRST_CORE_TESTS: list[FirstTest] = [
    FirstTest(
        "core_single_element",
        value={"$literal": [42]},
        expected=42,
        msg="$first should return the only element of a single-element array",
    ),
    FirstTest(
        "core_multi_element",
        value={"$literal": [1, 2, 3]},
        expected=1,
        msg="$first should return the first element of a multi-element array",
    ),
    FirstTest(
        "core_nested_arrays",
        value={"$literal": [[1, 2], [3, 4]]},
        expected=[1, 2],
        msg="$first should return the first top-level element without flattening",
    ),
    FirstTest(
        "core_nested_first",
        value={"$first": {"$literal": [[1, 2], [3, 4]]}},
        expected=1,
        msg="nested $first should unwrap one layer per call",
    ),
    FirstTest(
        "core_large_array",
        value={"$literal": list(range(10_000))},
        expected=0,
        msg="$first should return the first element of a large array",
    ),
    FirstTest(
        "core_array_of_empty_arrays",
        value={"$literal": [[], [], []]},
        expected=[],
        msg="$first of an array of empty arrays should return the first empty array",
    ),
    FirstTest(
        "core_mixed_bson_types",
        value={"$literal": ["hello", 1, True, None, 3.14]},
        expected="hello",
        msg="$first should return the first element regardless of mixed BSON types",
    ),
    FirstTest(
        "core_null_first_element",
        value={"$literal": [None, 2, 3]},
        expected=None,
        msg="$first should return None when the first element is null",
    ),
]

# Property [Falsy First Elements]: falsy values (empty string, zero, false,
# empty array, empty object) are preserved correctly as the first element.
FIRST_FALSY_TESTS: list[FirstTest] = [
    FirstTest(
        "falsy_empty_string",
        value={"$literal": ["", "x"]},
        expected="",
        msg="$first should preserve empty string as first element",
    ),
    FirstTest(
        "falsy_zero",
        value={"$literal": [0, 1]},
        expected=0,
        msg="$first should preserve zero as first element",
    ),
    FirstTest(
        "falsy_false",
        value={"$literal": [False, True]},
        expected=False,
        msg="$first should preserve false as first element",
    ),
    FirstTest(
        "falsy_empty_array",
        value={"$literal": [[], [1]]},
        expected=[],
        msg="$first should preserve empty array as first element",
    ),
    FirstTest(
        "falsy_empty_object",
        value={"$literal": [{}, {"a": 1}]},
        expected={},
        msg="$first should preserve empty object as first element",
    ),
]

# Property [Literal Unwrapping]: a single-element literal array is unwrapped
# at parse time. $first: ["hello"] becomes $first: "hello" (type error), while
# $first: [null] becomes $first: null (returns null). Field references bypass
# this unwrapping, so arrays pass through intact.
FIRST_LITERAL_UNWRAP_SUCCESS_TESTS: list[FirstTest] = [
    FirstTest(
        "literal_unwrap_null",
        value=[None],
        expected=None,
        msg="$first of [null] should unwrap to $first: null and produce null",
    ),
    FirstTest(
        "literal_unwrap_field_ref_single",
        value="$single",
        document={"single": ["hello"]},
        expected="hello",
        msg="$first of field ref to ['hello'] should return 'hello' without unwrapping",
    ),
    FirstTest(
        "literal_unwrap_field_ref_multi",
        value="$multi",
        document={"multi": ["a", "b"]},
        expected="a",
        msg="$first of field ref to ['a','b'] should return 'a' without unwrapping",
    ),
]

FIRST_CORE_ALL_TESTS = FIRST_CORE_TESTS + FIRST_FALSY_TESTS + FIRST_LITERAL_UNWRAP_SUCCESS_TESTS


@pytest.mark.parametrize("test_case", pytest_params(FIRST_CORE_ALL_TESTS))
def test_first_core(collection, test_case: FirstTest):
    """Test $first cases."""
    if test_case.document is not None:
        result = execute_expression_with_insert(
            collection, {"$first": test_case.value}, test_case.document
        )
    else:
        result = execute_expression(collection, {"$first": test_case.value})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
