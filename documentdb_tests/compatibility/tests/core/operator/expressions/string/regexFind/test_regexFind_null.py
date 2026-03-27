from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.framework.test_constants import MISSING
from documentdb_tests.compatibility.tests.core.operator.expressions.string.regexFind.utils.regexFind_common import (
    RegexFindTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import execute_expression

_PLACEHOLDER = object()
_NULL_PATTERNS = [
    (_PLACEHOLDER, "abc", "input"),
    ("hello", _PLACEHOLDER, "regex"),
    (_PLACEHOLDER, _PLACEHOLDER, "both"),
]


_MSG_MAP = {
    "input": "$regexFind should return null when input is {kind}",
    "regex": "$regexFind should return null when regex is {kind}",
    "both": "$regexFind should return null when both args are {kind}",
}


def _build_null_tests(null_value, prefix) -> list[RegexFindTest]:
    kind = "null" if null_value is None else "missing"
    return [
        RegexFindTest(
            f"{prefix}_{suffix}",
            input=null_value if _input is _PLACEHOLDER else _input,
            regex=null_value if _regex is _PLACEHOLDER else _regex,
            expected=None,
            msg=_MSG_MAP[suffix].format(kind=kind),
        )
        for _input, _regex, suffix in _NULL_PATTERNS
    ]


# Property [Null Propagation]: null in input or regex causes the result to be null.
REGEXFIND_NULL_TESTS = _build_null_tests(None, "null")

# Property [Null Propagation - missing]: missing fields in input or regex are treated as null.
REGEXFIND_MISSING_TESTS = _build_null_tests(MISSING, "missing")

# Property [Null Propagation - mixed]: combining null and missing across input and regex
# still produces null.
REGEXFIND_MIXED_NULL_TESTS: list[RegexFindTest] = [
    RegexFindTest(
        "mixed_null_input_missing_regex",
        input=None,
        regex=MISSING,
        expected=None,
        msg="$regexFind should return null for null input and missing regex",
    ),
    RegexFindTest(
        "mixed_missing_input_null_regex",
        input=MISSING,
        regex=None,
        expected=None,
        msg="$regexFind should return null for missing input and null regex",
    ),
]

# Property [Options Null]: null in options does not cause null propagation.
REGEXFIND_OPTIONS_NULL_TESTS: list[RegexFindTest] = [
    RegexFindTest(
        "options_null",
        input="hello",
        regex="hello",
        options=None,
        expected={"match": "hello", "idx": 0, "captures": []},
        msg="$regexFind should not null-propagate on null options",
    ),
]

# Property [Options Null - missing]: missing field in options does not cause null propagation.
REGEXFIND_OPTIONS_MISSING_TESTS: list[RegexFindTest] = [
    RegexFindTest(
        "options_missing",
        input="hello",
        regex="hello",
        options=MISSING,
        expected={"match": "hello", "idx": 0, "captures": []},
        msg="$regexFind should not null-propagate on missing options",
    ),
]

# Property [Null Propagation - expressions]: an expression that evaluates to null is treated
# identically to a null literal.
REGEXFIND_EXPR_NULL_TESTS: list[RegexFindTest] = [
    RegexFindTest(
        "expr_null_input",
        input={"$cond": [False, "hello", None]},
        regex="hello",
        expected=None,
        msg="$regexFind should null-propagate when expr input resolves to null",
    ),
    RegexFindTest(
        "expr_null_regex",
        input="hello",
        regex={"$cond": [False, "hello", None]},
        expected=None,
        msg="$regexFind should null-propagate when expr regex resolves to null",
    ),
]

# Property [Null Precedence]: null propagation from regex takes precedence over bad option flag
# validation.
REGEXFIND_PRECEDENCE_SUCCESS_TESTS: list[RegexFindTest] = [
    RegexFindTest(
        "precedence_null_regex_over_bad_option",
        input="abc",
        regex=None,
        options="z",
        expected=None,
        msg="$regexFind null regex should take precedence over bad option",
    ),
]

REGEXFIND_NULL_ALL_TESTS = (
    REGEXFIND_NULL_TESTS
    + REGEXFIND_MISSING_TESTS
    + REGEXFIND_MIXED_NULL_TESTS
    + REGEXFIND_OPTIONS_NULL_TESTS
    + REGEXFIND_OPTIONS_MISSING_TESTS
    + REGEXFIND_EXPR_NULL_TESTS
    + REGEXFIND_PRECEDENCE_SUCCESS_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(REGEXFIND_NULL_ALL_TESTS))
def test_regexfind_cases(collection, test_case: RegexFindTest):
    """Test $regexFind null propagation cases."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
