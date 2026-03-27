from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.compatibility.tests.core.operator.expressions.string.regexMatch.utils.regexMatch_common import (
    RegexMatchTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import execute_expression

# Property [Expression Arguments]: input, regex, and options accept expressions that resolve to
# the appropriate type.
REGEXMATCH_EXPR_TESTS: list[RegexMatchTest] = [
    RegexMatchTest(
        "expr_input",
        input={"$concat": ["hel", "lo"]},
        regex="hello",
        expected=True,
        msg="$regexMatch should accept expression for input",
    ),
    RegexMatchTest(
        "expr_regex",
        input="hello",
        regex={"$concat": ["hel", "lo"]},
        expected=True,
        msg="$regexMatch should accept expression for regex",
    ),
    RegexMatchTest(
        "expr_options",
        input="HELLO",
        regex="hello",
        options={"$concat": ["", "i"]},
        expected=True,
        msg="$regexMatch should accept expression for options",
    ),
    RegexMatchTest(
        "expr_literal_dollar_regex",
        input="price: $100",
        regex={"$literal": "\\$[0-9]+"},
        expected=True,
        msg="$regexMatch should accept $literal for dollar in regex",
    ),
]


REGEXMATCH_LITERAL_INPUT_TESTS: list[RegexMatchTest] = [
    RegexMatchTest(
        "edge_dollar_input_is_field_ref",
        input="$nonexistent",
        regex="\\$nonexistent",
        expected=False,
        msg="$regexMatch should treat dollar-prefixed input as field ref",
    ),
]

# Property [Edge Cases]: empty strings, large inputs, and control characters are handled
# correctly.
REGEXMATCH_EDGE_TESTS: list[RegexMatchTest] = [
    RegexMatchTest(
        "edge_empty_input_empty_regex",
        input="",
        regex="",
        expected=True,
        msg="$regexMatch should match empty regex on empty input",
    ),
    RegexMatchTest(
        "edge_nonempty_input_empty_regex",
        input="hello",
        regex="",
        expected=True,
        msg="$regexMatch empty regex should match any input",
    ),
    RegexMatchTest(
        "edge_empty_input_nonempty_regex",
        input="",
        regex="abc",
        expected=False,
        msg="$regexMatch should return false for no match on empty input",
    ),
    RegexMatchTest(
        "edge_empty_input_dotstar",
        input="",
        regex=".*",
        expected=True,
        msg="$regexMatch .* should match empty input",
    ),
    RegexMatchTest(
        "edge_empty_input_anchored_empty",
        input="",
        regex="^$",
        expected=True,
        msg="$regexMatch ^$ should match empty input",
    ),
    RegexMatchTest(
        "edge_anchored_full_match",
        input="hello",
        regex="^hello$",
        expected=True,
        msg="$regexMatch anchored pattern should match full string",
    ),
    RegexMatchTest(
        "edge_anchored_partial_no_match",
        input="hello world",
        regex="^hello$",
        expected=False,
        msg="$regexMatch anchored pattern should not match partial",
    ),
    RegexMatchTest(
        "edge_partial_match",
        input="hello world",
        regex="world",
        expected=True,
        msg="$regexMatch should match substring of input",
    ),
    RegexMatchTest(
        "edge_newline",
        input="hello\nworld",
        regex="world",
        expected=True,
        msg="$regexMatch should match across newline",
    ),
    RegexMatchTest(
        "edge_tab",
        input="hello\tworld",
        regex="world",
        expected=True,
        msg="$regexMatch should match across tab",
    ),
    RegexMatchTest(
        "edge_null_byte",
        input="hello\x00world",
        regex="world",
        expected=True,
        msg="$regexMatch should match across null byte",
    ),
    RegexMatchTest(
        "edge_carriage_return",
        input="hello\rworld",
        regex="world",
        expected=True,
        msg="$regexMatch should match across carriage return",
    ),
    RegexMatchTest(
        "edge_s_no_nbsp",
        input="\u00a0hello",
        regex="\\s",
        expected=False,
        msg="$regexMatch \\s should not match NBSP",
    ),
]

REGEXMATCH_MATCHING_ALL_TESTS = (
    REGEXMATCH_EXPR_TESTS + REGEXMATCH_LITERAL_INPUT_TESTS + REGEXMATCH_EDGE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(REGEXMATCH_MATCHING_ALL_TESTS))
def test_regexmatch_cases(collection, test_case: RegexMatchTest):
    """Test $regexMatch matching behavior cases."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
