from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.framework.test_constants import MISSING
from documentdb_tests.compatibility.tests.core.operator.expressions.string.ltrim.utils.ltrim_common import (
    _OMIT,
    LtrimTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import execute_expression

# Argument shapes for null/missing tests. _PLACEHOLDER is replaced with None or MISSING.
_PLACEHOLDER = object()
_NULL_PATTERNS = [
    (_PLACEHOLDER, _OMIT, "input_default_chars", "input is {kind} with default chars"),
    (_PLACEHOLDER, "abc", "input_custom_chars", "input is {kind} with custom chars"),
    ("hello", _PLACEHOLDER, "chars_valid_input", "chars is {kind} with valid string input"),
    (_PLACEHOLDER, _PLACEHOLDER, "both", "both input and chars are {kind}"),
    # Null/missing input takes precedence over non-string chars (no error raised).
    (_PLACEHOLDER, 123, "precedence_chars_int", "input is {kind} even with non-string chars"),
]


def _build_null_tests(null_value, prefix) -> list[LtrimTest]:
    return [
        LtrimTest(
            f"{prefix}_{suffix}",
            input=null_value if _input is _PLACEHOLDER else _input,
            chars=null_value if _chars is _PLACEHOLDER else _chars,
            expected=None,
            msg=f"$ltrim should return null when {msg_tmpl.format(kind=prefix)}",
        )
        for _input, _chars, suffix, msg_tmpl in _NULL_PATTERNS
    ]


# Property [Null Propagation]: when either input or chars is null, the result is null.
LTRIM_NULL_TESTS = _build_null_tests(None, "null")

# Property [Null Propagation - missing]: missing fields are treated as null.
LTRIM_MISSING_TESTS = _build_null_tests(MISSING, "missing")

# Property [Null Propagation - mixed null and missing]: combining null and missing across
# positions still produces null.
LTRIM_MIXED_NULL_TESTS: list[LtrimTest] = [
    LtrimTest(
        "mixed_null_input_missing_chars",
        input=None,
        chars=MISSING,
        expected=None,
        msg="$ltrim should return null when input is null and chars is missing",
    ),
    LtrimTest(
        "mixed_missing_input_null_chars",
        input=MISSING,
        chars=None,
        expected=None,
        msg="$ltrim should return null when input is missing and chars is null",
    ),
]

LTRIM_NULL_ALL_TESTS = LTRIM_NULL_TESTS + LTRIM_MISSING_TESTS + LTRIM_MIXED_NULL_TESTS


@pytest.mark.parametrize("test_case", pytest_params(LTRIM_NULL_ALL_TESTS))
def test_ltrim_null(collection, test_case: LtrimTest):
    """Test $ltrim null propagation cases."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
