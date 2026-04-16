from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.accumulator.last.utils.last_common import (  # noqa: E501
    LastTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Core Element Extraction]: $last returns the last element of an
# array without flattening.
LAST_CORE_TESTS: list[LastTest] = [
    LastTest(
        "core_single_element",
        value={"$literal": [42]},
        expected=42,
        msg="$last should return the only element of a single-element array",
    ),
    LastTest(
        "core_multi_element",
        value={"$literal": [1, 2, 3]},
        expected=3,
        msg="$last should return the last element of a multi-element array",
    ),
    LastTest(
        "core_nested_arrays",
        value={"$literal": [[1, 2], [3, 4]]},
        expected=[3, 4],
        msg="$last should return the last top-level element without flattening",
    ),
    LastTest(
        "core_nested_last",
        value={"$last": {"$literal": [[1, 2], [3, 4]]}},
        expected=4,
        msg="nested $last should unwrap one layer per call",
    ),
    LastTest(
        "core_large_array",
        value={"$literal": list(range(10_000))},
        expected=9_999,
        msg="$last should return the last element of a large array",
    ),
    LastTest(
        "core_array_of_empty_arrays",
        value={"$literal": [[], [], []]},
        expected=[],
        msg="$last of an array of empty arrays should return the last empty array",
    ),
    LastTest(
        "core_mixed_bson_types",
        value={"$literal": [1, "hello", True, None, 3.14]},
        expected=3.14,
        msg="$last should return the last element regardless of mixed BSON types",
    ),
    LastTest(
        "core_null_last_element",
        value={"$literal": [1, 2, None]},
        expected=None,
        msg="$last should return None when the last element is null",
    ),
]

# Property [Falsy Last Elements]: falsy values (empty string, zero, false,
# empty array, empty object) are preserved correctly as the last element.
LAST_FALSY_TESTS: list[LastTest] = [
    LastTest(
        "falsy_empty_string",
        value={"$literal": ["x", ""]},
        expected="",
        msg="$last should preserve empty string as last element",
    ),
    LastTest(
        "falsy_zero",
        value={"$literal": [1, 0]},
        expected=0,
        msg="$last should preserve zero as last element",
    ),
    LastTest(
        "falsy_false",
        value={"$literal": [True, False]},
        expected=False,
        msg="$last should preserve false as last element",
    ),
    LastTest(
        "falsy_empty_array",
        value={"$literal": [[1], []]},
        expected=[],
        msg="$last should preserve empty array as last element",
    ),
    LastTest(
        "falsy_empty_object",
        value={"$literal": [{"a": 1}, {}]},
        expected={},
        msg="$last should preserve empty object as last element",
    ),
]

# Property [Literal Unwrapping]: a single-element literal array is unwrapped
# at parse time. $last: ["hello"] becomes $last: "hello" (type error), while
# $last: [null] becomes $last: null (returns null). Field references bypass
# this unwrapping, so arrays pass through intact.
LAST_LITERAL_UNWRAP_SUCCESS_TESTS: list[LastTest] = [
    LastTest(
        "literal_unwrap_null",
        value=[None],
        expected=None,
        msg="$last of [null] should unwrap to $last: null and produce null",
    ),
    LastTest(
        "literal_unwrap_field_ref_single",
        value="$single",
        document={"single": ["hello"]},
        expected="hello",
        msg="$last of field ref to ['hello'] should return 'hello' without unwrapping",
    ),
    LastTest(
        "literal_unwrap_field_ref_multi",
        value="$multi",
        document={"multi": ["a", "b"]},
        expected="b",
        msg="$last of field ref to ['a','b'] should return 'b' without unwrapping",
    ),
]

LAST_CORE_ALL_TESTS = LAST_CORE_TESTS + LAST_FALSY_TESTS + LAST_LITERAL_UNWRAP_SUCCESS_TESTS


@pytest.mark.parametrize("test_case", pytest_params(LAST_CORE_ALL_TESTS))
def test_last_core(collection, test_case: LastTest):
    """Test $last cases."""
    if test_case.document is not None:
        result = execute_expression_with_insert(
            collection, {"$last": test_case.value}, test_case.document
        )
    else:
        result = execute_expression(collection, {"$last": test_case.value})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
