from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.framework.test_constants import MISSING
from documentdb_tests.compatibility.tests.core.operator.expressions.string.regexFindAll.utils.regexFindAll_common import (
    RegexFindAllTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import execute_expression

# Property [Null Propagation]: null in input or regex causes the result to be an empty array.
_PLACEHOLDER = object()
_NULL_PATTERNS = [
    (_PLACEHOLDER, "abc", "input"),
    ("hello", _PLACEHOLDER, "regex"),
    (_PLACEHOLDER, _PLACEHOLDER, "both"),
]


def _build_null_tests(null_value, prefix) -> list[RegexFindAllTest]:
    _MSG_MAP = {
        "input": f"$regexFindAll should return empty array when input is {prefix}",
        "regex": f"$regexFindAll should return empty array when regex is {prefix}",
        "both": f"$regexFindAll should return empty array when both input and regex are {prefix}",
    }
    return [
        RegexFindAllTest(
            f"{prefix}_{suffix}",
            input=null_value if _input is _PLACEHOLDER else _input,
            regex=null_value if regex is _PLACEHOLDER else regex,
            expected=[],
            msg=_MSG_MAP[suffix],
        )
        for _input, regex, suffix in _NULL_PATTERNS
    ]


REGEXFINDALL_NULL_TESTS = _build_null_tests(None, "null")

# Property [Null Propagation - missing]: missing fields in input or regex are treated as null.
REGEXFINDALL_MISSING_TESTS = _build_null_tests(MISSING, "missing")

# Property [Null Propagation - mixed]: combining null and missing across input and regex still
# produces an empty array.
REGEXFINDALL_MIXED_NULL_TESTS: list[RegexFindAllTest] = [
    RegexFindAllTest(
        "mixed_null_input_missing_regex",
        input=None,
        regex=MISSING,
        expected=[],
        msg="$regexFindAll should return empty array when input is null and regex is missing",
    ),
    RegexFindAllTest(
        "mixed_missing_input_null_regex",
        input=MISSING,
        regex=None,
        expected=[],
        msg="$regexFindAll should return empty array when input is missing and regex is null",
    ),
]

# Property [Options Null]: null in options does not cause null propagation.
REGEXFINDALL_OPTIONS_NULL_TESTS: list[RegexFindAllTest] = [
    RegexFindAllTest(
        "options_null",
        input="hello",
        regex="hello",
        options=None,
        expected=[{"match": "hello", "idx": 0, "captures": []}],
        msg="$regexFindAll should match normally when options is null",
    ),
]

# Property [Options Null - missing]: missing field in options does not cause null propagation.
REGEXFINDALL_OPTIONS_MISSING_TESTS: list[RegexFindAllTest] = [
    RegexFindAllTest(
        "options_missing",
        input="hello",
        regex="hello",
        options=MISSING,
        expected=[{"match": "hello", "idx": 0, "captures": []}],
        msg="$regexFindAll should match normally when options is a missing field",
    ),
]


# Property [Null Propagation - expressions]: an expression that evaluates to null is treated
# identically to a null literal.
REGEXFINDALL_EXPR_NULL_TESTS: list[RegexFindAllTest] = [
    RegexFindAllTest(
        "expr_null_input",
        input={"$cond": [False, "hello", None]},
        regex="hello",
        expected=[],
        msg="$regexFindAll should return empty array when input expression evaluates to null",
    ),
    RegexFindAllTest(
        "expr_null_regex",
        input="hello",
        regex={"$cond": [False, "hello", None]},
        expected=[],
        msg="$regexFindAll should return empty array when regex expression evaluates to null",
    ),
]

REGEXFINDALL_NULL_ALL_TESTS = (
    REGEXFINDALL_NULL_TESTS
    + REGEXFINDALL_MISSING_TESTS
    + REGEXFINDALL_MIXED_NULL_TESTS
    + REGEXFINDALL_OPTIONS_NULL_TESTS
    + REGEXFINDALL_OPTIONS_MISSING_TESTS
    + REGEXFINDALL_EXPR_NULL_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(REGEXFINDALL_NULL_ALL_TESTS))
def test_regexfindall_null(collection, test_case: RegexFindAllTest):
    """Test $regexFindAll null propagation cases."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
