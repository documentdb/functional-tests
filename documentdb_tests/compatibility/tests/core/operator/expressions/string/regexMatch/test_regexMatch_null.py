from __future__ import annotations

import pytest
from bson import Regex

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.framework.test_constants import MISSING
from documentdb_tests.compatibility.tests.core.operator.expressions.string.regexMatch.utils.regexMatch_common import (
    RegexMatchTest,
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
    "input": "$regexMatch should return false when input is {kind}",
    "regex": "$regexMatch should return false when regex is {kind}",
    "both": "$regexMatch should return false when both args are {kind}",
}


def _build_null_tests(null_value, prefix) -> list[RegexMatchTest]:
    kind = "null" if null_value is None else "missing"
    return [
        RegexMatchTest(
            f"{prefix}_{suffix}",
            input=null_value if _input is _PLACEHOLDER else _input,
            regex=null_value if _regex is _PLACEHOLDER else _regex,
            expected=False,
            msg=_MSG_MAP[suffix].format(kind=kind),
        )
        for _input, _regex, suffix in _NULL_PATTERNS
    ]


# Property [Null Propagation]: null in input or regex causes the result to be false.
REGEXMATCH_NULL_TESTS = _build_null_tests(None, "null")

# Property [Null Propagation - missing]: missing fields in input or regex are treated as null.
REGEXMATCH_MISSING_TESTS = _build_null_tests(MISSING, "missing")

# Property [Null Propagation - mixed]: combining null and missing across input and regex
# still produces false.
REGEXMATCH_MIXED_NULL_TESTS: list[RegexMatchTest] = [
    RegexMatchTest(
        "mixed_null_input_missing_regex",
        input=None,
        regex=MISSING,
        expected=False,
        msg="$regexMatch should return false for null input and missing regex",
    ),
    RegexMatchTest(
        "mixed_missing_input_null_regex",
        input=MISSING,
        regex=None,
        expected=False,
        msg="$regexMatch should return false for missing input and null regex",
    ),
]

# Property [Options Null]: null in options does not cause the result to be false; the match
# proceeds normally.
REGEXMATCH_OPTIONS_NULL_TESTS: list[RegexMatchTest] = [
    RegexMatchTest(
        "options_null",
        input="hello",
        regex="hello",
        options=None,
        expected=True,
        msg="$regexMatch should not return false on null options",
    ),
]

# Property [Options Null - missing]: missing field in options does not cause the result to be
# false; the match proceeds normally.
REGEXMATCH_OPTIONS_MISSING_TESTS: list[RegexMatchTest] = [
    RegexMatchTest(
        "options_missing",
        input="hello",
        regex="hello",
        options=MISSING,
        expected=True,
        msg="$regexMatch should not return false on missing options",
    ),
    # Missing options does not conflict with BSON Regex flags.
    RegexMatchTest(
        "options_no_conflict_missing_options_with_flags",
        input="HELLO",
        regex=Regex("hello", "i"),
        options=MISSING,
        expected=True,
        msg="$regexMatch missing options should not conflict with BSON flags",
    ),
]


REGEXMATCH_EXPR_NULL_TESTS: list[RegexMatchTest] = [
    RegexMatchTest(
        "expr_null_input",
        input={"$cond": [False, "hello", None]},
        regex="hello",
        expected=False,
        msg="$regexMatch should return false when expr input resolves to null",
    ),
    RegexMatchTest(
        "expr_null_regex",
        input="hello",
        regex={"$cond": [False, "hello", None]},
        expected=False,
        msg="$regexMatch should return false when expr regex resolves to null",
    ),
]


# Property [Null Precedence]: null propagation from regex takes precedence over bad option flag
# validation.
REGEXMATCH_PRECEDENCE_SUCCESS_TESTS: list[RegexMatchTest] = [
    RegexMatchTest(
        "precedence_null_regex_over_bad_option",
        input="abc",
        regex=None,
        options="z",
        expected=False,
        msg="$regexMatch null regex should take precedence over bad option",
    ),
]

REGEXMATCH_NULL_ALL_TESTS = (
    REGEXMATCH_NULL_TESTS
    + REGEXMATCH_MISSING_TESTS
    + REGEXMATCH_MIXED_NULL_TESTS
    + REGEXMATCH_OPTIONS_NULL_TESTS
    + REGEXMATCH_OPTIONS_MISSING_TESTS
    + REGEXMATCH_EXPR_NULL_TESTS
    + REGEXMATCH_PRECEDENCE_SUCCESS_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(REGEXMATCH_NULL_ALL_TESTS))
def test_regexmatch_cases(collection, test_case: RegexMatchTest):
    """Test $regexMatch null propagation cases."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
