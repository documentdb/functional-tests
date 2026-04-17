from __future__ import annotations

from typing import Any

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING

from .utils.replaceOne_common import (
    ReplaceOneTest,
    _expr,
)

# Property [Null Propagation]: if any argument is null or missing, the result
# is null, uniformly across all three argument positions.
_PLACEHOLDER = object()
_NULL_PATTERNS: list[tuple[Any, Any, Any, str]] = [
    (_PLACEHOLDER, "a", "b", "input"),
    ("hello", _PLACEHOLDER, "b", "find"),
    ("hello", "a", _PLACEHOLDER, "replacement"),
    (_PLACEHOLDER, _PLACEHOLDER, "b", "input_and_find"),
    (_PLACEHOLDER, "a", _PLACEHOLDER, "input_and_replacement"),
    ("hello", _PLACEHOLDER, _PLACEHOLDER, "find_and_replacement"),
    (_PLACEHOLDER, _PLACEHOLDER, _PLACEHOLDER, "all"),
]


def _build_null_tests(null_value, prefix) -> list[ReplaceOneTest]:
    return [
        ReplaceOneTest(
            f"{prefix}_{suffix}",
            input=null_value if i is _PLACEHOLDER else i,
            find=null_value if f is _PLACEHOLDER else f,
            replacement=null_value if r is _PLACEHOLDER else r,
            expected=None,
            msg=f"$replaceOne {prefix} {suffix}",
        )
        for i, f, r, suffix in _NULL_PATTERNS
    ]


REPLACEONE_NULL_TESTS = _build_null_tests(None, "null")
REPLACEONE_MISSING_TESTS = _build_null_tests(MISSING, "missing")

REPLACEONE_MIXED_NULL_TESTS: list[ReplaceOneTest] = [
    ReplaceOneTest(
        "null_input_missing_find",
        input=None,
        find=MISSING,
        replacement="b",
        expected=None,
        msg="$replaceOne should return null for null input missing find",
    ),
    ReplaceOneTest(
        "missing_input_null_find",
        input=MISSING,
        find=None,
        replacement="b",
        expected=None,
        msg="$replaceOne should return null for missing input null find",
    ),
    ReplaceOneTest(
        "null_find_missing_replacement",
        input="hello",
        find=None,
        replacement=MISSING,
        expected=None,
        msg="$replaceOne should return null for null find missing replacement",
    ),
    ReplaceOneTest(
        "missing_find_null_replacement",
        input="hello",
        find=MISSING,
        replacement=None,
        expected=None,
        msg="$replaceOne should return null for missing find null replacement",
    ),
    ReplaceOneTest(
        "null_input_missing_replacement",
        input=None,
        find="a",
        replacement=MISSING,
        expected=None,
        msg="$replaceOne should return null for null input missing replacement",
    ),
    ReplaceOneTest(
        "missing_input_null_replacement",
        input=MISSING,
        find="a",
        replacement=None,
        expected=None,
        msg="$replaceOne should return null for missing input null replacement",
    ),
]

REPLACEONE_NULL_ALL_TESTS = (
    REPLACEONE_NULL_TESTS + REPLACEONE_MISSING_TESTS + REPLACEONE_MIXED_NULL_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(REPLACEONE_NULL_ALL_TESTS))
def test_replaceone_null_cases(collection, test_case: ReplaceOneTest):
    """Test $replaceOne null propagation cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
