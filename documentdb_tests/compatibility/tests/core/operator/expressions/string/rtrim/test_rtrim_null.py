from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING

from .utils.rtrim_common import (
    _OMIT,
    RtrimTest,
    _expr,
)

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


def _build_null_tests(null_value, prefix) -> list[RtrimTest]:
    return [
        RtrimTest(
            f"{prefix}_{suffix}",
            input=null_value if _input is _PLACEHOLDER else _input,
            chars=null_value if _chars is _PLACEHOLDER else _chars,
            expected=None,
            msg=f"$rtrim should return null when {msg_tmpl.format(kind=prefix)}",
        )
        for _input, _chars, suffix, msg_tmpl in _NULL_PATTERNS
    ]


# Property [Null Propagation]: when either input or chars is null, the result is null.
RTRIM_NULL_TESTS = _build_null_tests(None, "null")

# Property [Null Propagation - missing]: missing fields are treated as null.
RTRIM_MISSING_TESTS = _build_null_tests(MISSING, "missing")

# Property [Null Propagation - mixed null and missing]: combining null and missing across
# positions still produces null.
RTRIM_MIXED_NULL_TESTS: list[RtrimTest] = [
    RtrimTest(
        "mixed_null_input_missing_chars",
        input=None,
        chars=MISSING,
        expected=None,
        msg="$rtrim should return null when input is null and chars is missing",
    ),
    RtrimTest(
        "mixed_missing_input_null_chars",
        input=MISSING,
        chars=None,
        expected=None,
        msg="$rtrim should return null when input is missing and chars is null",
    ),
]

RTRIM_NULL_ALL_TESTS = RTRIM_NULL_TESTS + RTRIM_MISSING_TESTS + RTRIM_MIXED_NULL_TESTS


@pytest.mark.parametrize("test_case", pytest_params(RTRIM_NULL_ALL_TESTS))
def test_rtrim_null(collection, test_case: RtrimTest):
    """Test $rtrim null propagation."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
