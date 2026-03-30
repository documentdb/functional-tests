from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.framework.test_constants import MISSING
from documentdb_tests.compatibility.tests.core.operator.expressions.string.concat.utils.concat_common import (
    ConcatTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import execute_expression

# Property [Null Propagation]: if any argument is null, the result is null.
# Argument shapes where _PLACEHOLDER is the null-producing value.
_PLACEHOLDER = object()
_NULL_PATTERNS = [
    ([_PLACEHOLDER], "single"),
    (["hello", _PLACEHOLDER], "last"),
    ([_PLACEHOLDER, "hello"], "first"),
    (["a", _PLACEHOLDER, "b"], "middle"),
    ([_PLACEHOLDER, _PLACEHOLDER], "all"),
    ([_PLACEHOLDER, _PLACEHOLDER, _PLACEHOLDER], "many"),
    (["a", "b", "c", _PLACEHOLDER, "d", "e"], "among_many_strings"),
]


def _build_null_tests(null_value, prefix) -> list[ConcatTest]:
    """Generate test cases by replacing _PLACEHOLDER with the given null value."""
    return [
        ConcatTest(
            f"{prefix}_{suffix}",
            args=[null_value if a is _PLACEHOLDER else a for a in args],
            expected=None,
            msg=f"$concat should return null when {prefix} value is in position: {suffix}",
        )
        for args, suffix in _NULL_PATTERNS
    ]


# Explicit None. Used by inline, insert, and mixed tests.
CONCAT_NULL_TESTS = _build_null_tests(None, "null")

# Missing field references (resolve to null at runtime).
# Only meaningful for inline since there is no stored field to read.
CONCAT_MISSING_TESTS = _build_null_tests(MISSING, "missing")

CONCAT_MIXED_NULL_TESTS = [
    ConcatTest(
        "null_and_missing",
        args=[None, MISSING],
        expected=None,
        msg="$concat should return null when args contain both null and missing",
    ),
    ConcatTest(
        "null_and_missing_among_strings",
        args=["a", None, MISSING, "b"],
        expected=None,
        msg="$concat should return null when null and missing appear among strings",
    ),
]

# Property [Error Precedence - Null Wins]: when null or missing appears before a type-invalid
# argument in left-to-right order, null propagation takes precedence and the result is null.
CONCAT_ERROR_PREC_NULL_WINS_TESTS: list[ConcatTest] = [
    ConcatTest(
        "error_prec_null_before_int",
        args=[None, 42],
        expected=None,
        msg="$concat should return null when null precedes type-invalid argument",
    ),
    ConcatTest(
        "error_prec_str_null_int",
        args=["hello", None, 42],
        expected=None,
        msg="$concat should return null when null appears between string and invalid arg",
    ),
    ConcatTest(
        "error_prec_null_before_two_invalid",
        args=[None, 42, True],
        expected=None,
        msg="$concat should return null when null precedes multiple invalid args",
    ),
    ConcatTest(
        "error_prec_missing_before_int",
        args=[MISSING, 42],
        expected=None,
        msg="$concat should return null when missing precedes type-invalid argument",
    ),
]

CONCAT_NULL_ALL_TESTS = (
    CONCAT_NULL_TESTS
    + CONCAT_MISSING_TESTS
    + CONCAT_MIXED_NULL_TESTS
    + CONCAT_ERROR_PREC_NULL_WINS_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(CONCAT_NULL_ALL_TESTS))
def test_concat_null_cases(collection, test_case: ConcatTest):
    """Test $concat null propagation cases."""
    result = execute_expression(collection, {"$concat": test_case.args})
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
