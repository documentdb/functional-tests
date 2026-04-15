from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

from .utils.regexFindAll_common import (
    RegexFindAllTest,
    _expr,
)

# Property [Captures Behavior]: captures array length equals the number of capture groups, in
# pattern order. Unmatched branches produce null. Non-capturing groups are excluded. Nested groups
# are each represented. Each result document has its own independent captures array.
REGEXFINDALL_CAPTURES_TESTS: list[RegexFindAllTest] = [
    RegexFindAllTest(
        "captures_single_group",
        input="abc123",
        regex="([0-9]+)",
        expected=[{"match": "123", "idx": 3, "captures": ["123"]}],
        msg="$regexFindAll should populate captures with single group match",
    ),
    # Order matches left-to-right group appearance.
    RegexFindAllTest(
        "captures_two_groups_order",
        input="John Smith",
        regex="(\\w+) (\\w+)",
        expected=[{"match": "John Smith", "idx": 0, "captures": ["John", "Smith"]}],
        msg="$regexFindAll should order captures left-to-right by group position",
    ),
    # Second alternation branch unmatched produces null in that position.
    RegexFindAllTest(
        "captures_unmatched_branch",
        input="cat",
        regex="(cat)|(dog)",
        expected=[{"match": "cat", "idx": 0, "captures": ["cat", None]}],
        msg="$regexFindAll should produce null for unmatched alternation branch capture",
    ),
    # Non-capturing group excluded from captures.
    RegexFindAllTest(
        "captures_non_capturing_excluded",
        input="abc123",
        regex="(?:abc)([0-9]+)",
        expected=[{"match": "abc123", "idx": 0, "captures": ["123"]}],
        msg="$regexFindAll should exclude non-capturing group from captures",
    ),
    # Nested groups: outer then inner, left to right.
    RegexFindAllTest(
        "captures_nested_groups",
        input="abc",
        regex="((a)(b))c",
        expected=[{"match": "abc", "idx": 0, "captures": ["ab", "a", "b"]}],
        msg="$regexFindAll should list nested captures outer-then-inner left-to-right",
    ),
    # Named group included in captures.
    RegexFindAllTest(
        "captures_named_groups",
        input="abc123",
        regex="(?P<word>[a-z]+)(?P<num>[0-9]+)",
        expected=[{"match": "abc123", "idx": 0, "captures": ["abc", "123"]}],
        msg="$regexFindAll should include named groups in captures array",
    ),
    # Empty capture group captures empty string.
    RegexFindAllTest(
        "captures_empty_group",
        input="abc",
        regex="()(abc)",
        expected=[{"match": "abc", "idx": 0, "captures": ["", "abc"]}],
        msg="$regexFindAll should capture empty string for empty capture group",
    ),
    # Captures vary across multiple matches. Same group matches different content in each result
    # document.
    RegexFindAllTest(
        "captures_multi_match_varying",
        input="cat dog",
        regex="(\\w+)",
        expected=[
            {"match": "cat", "idx": 0, "captures": ["cat"]},
            {"match": "dog", "idx": 4, "captures": ["dog"]},
        ],
        msg="$regexFindAll should produce independent captures for each match",
    ),
    # A capture group participates in one match but not another. The alternation (cat)|(dog) has two
    # groups. Each match populates one and leaves the other null.
    RegexFindAllTest(
        "captures_group_participates_in_some",
        input="cat dog",
        regex="(cat)|(dog)",
        expected=[
            {"match": "cat", "idx": 0, "captures": ["cat", None]},
            {"match": "dog", "idx": 4, "captures": [None, "dog"]},
        ],
        msg="$regexFindAll should set null for non-participating group in each match",
    ),
]


# Property [Edge Cases]: empty strings, large inputs, and control characters are handled correctly.
REGEXFINDALL_EDGE_TESTS: list[RegexFindAllTest] = [
    # Empty input with empty regex matches once at position 0.
    RegexFindAllTest(
        "edge_empty_input_empty_regex",
        input="",
        regex="",
        expected=[{"match": "", "idx": 0, "captures": []}],
        msg="$regexFindAll should return one empty match when both input and regex are empty",
    ),
    # Empty regex on non-empty input matches at every code point position.
    RegexFindAllTest(
        "edge_nonempty_input_empty_regex",
        input="hello",
        regex="",
        expected=[
            {"match": "", "idx": 0, "captures": []},
            {"match": "", "idx": 1, "captures": []},
            {"match": "", "idx": 2, "captures": []},
            {"match": "", "idx": 3, "captures": []},
            {"match": "", "idx": 4, "captures": []},
        ],
        msg="$regexFindAll should match empty regex at every code point position",
    ),
    # Empty input with non-empty regex returns empty array.
    RegexFindAllTest(
        "edge_empty_input_nonempty_regex",
        input="",
        regex="abc",
        expected=[],
        msg="$regexFindAll should return empty array when input is empty and regex is non-empty",
    ),
    # Large input with many matches. 5_000 is an arbitrary high count that remains
    # performant; scaling to STRING_SIZE_LIMIT_BYTES would produce ~8M matches and hang.
    RegexFindAllTest(
        "edge_large_input_many_matches",
        input="ab" * 5_000,
        regex="ab",
        expected=[{"match": "ab", "idx": i * 2, "captures": []} for i in range(5_000)],
        msg="$regexFindAll should return all 5000 matches from a large repeated input",
    ),
    # Newline in input.
    RegexFindAllTest(
        "edge_newline",
        input="hello\nworld",
        regex="world",
        expected=[{"match": "world", "idx": 6, "captures": []}],
        msg="$regexFindAll should match across newline in input",
    ),
    # Tab in input.
    RegexFindAllTest(
        "edge_tab",
        input="hello\tworld",
        regex="world",
        expected=[{"match": "world", "idx": 6, "captures": []}],
        msg="$regexFindAll should match across tab in input",
    ),
    # Null byte in input.
    RegexFindAllTest(
        "edge_null_byte",
        input="hello\x00world",
        regex="world",
        expected=[{"match": "world", "idx": 6, "captures": []}],
        msg="$regexFindAll should match after embedded null byte in input",
    ),
    # Carriage return in input.
    RegexFindAllTest(
        "edge_carriage_return",
        input="hello\rworld",
        regex="world",
        expected=[{"match": "world", "idx": 6, "captures": []}],
        msg="$regexFindAll should match across carriage return in input",
    ),
    # Multiple matches spanning newline boundaries.
    RegexFindAllTest(
        "edge_matches_across_newlines",
        input="abc\nabc\nabc",
        regex="abc",
        expected=[
            {"match": "abc", "idx": 0, "captures": []},
            {"match": "abc", "idx": 4, "captures": []},
            {"match": "abc", "idx": 8, "captures": []},
        ],
        msg="$regexFindAll should find all matches spanning newline boundaries",
    ),
]

# Property [Multiple Match Enumeration]: all non-overlapping matches are returned in position order.
REGEXFINDALL_MULTI_MATCH_TESTS: list[RegexFindAllTest] = [
    # Greedy quantifier consumes maximum input, reducing match count.
    RegexFindAllTest(
        "multi_greedy_fewer_matches",
        input="aaa",
        regex="a+",
        expected=[{"match": "aaa", "idx": 0, "captures": []}],
        msg="$regexFindAll greedy quantifier should consume maximum input in one match",
    ),
    # Lazy quantifier consumes minimum input, increasing match count.
    RegexFindAllTest(
        "multi_nongreedy_more_matches",
        input="aaa",
        regex="a+?",
        expected=[
            {"match": "a", "idx": 0, "captures": []},
            {"match": "a", "idx": 1, "captures": []},
            {"match": "a", "idx": 2, "captures": []},
        ],
        msg="$regexFindAll lazy quantifier should produce one match per character",
    ),
    # Pattern matching every character produces one match per code point.
    RegexFindAllTest(
        "multi_per_character",
        input="abc",
        regex=".",
        expected=[
            {"match": "a", "idx": 0, "captures": []},
            {"match": "b", "idx": 1, "captures": []},
            {"match": "c", "idx": 2, "captures": []},
        ],
        msg="$regexFindAll dot pattern should produce one match per code point",
    ),
    # Matches from different branches returned in position order.
    RegexFindAllTest(
        "multi_alternation_position_order",
        input="catXdogXcat",
        regex="cat|dog",
        expected=[
            {"match": "cat", "idx": 0, "captures": []},
            {"match": "dog", "idx": 4, "captures": []},
            {"match": "cat", "idx": 8, "captures": []},
        ],
        msg="$regexFindAll should return alternation matches in position order",
    ),
]

# Property [Zero-Width Match Behavior]: zero-width matches are enumerated across the input, with
# the engine advancing by one code point after each to avoid infinite repetition.
REGEXFINDALL_ZERO_WIDTH_TESTS: list[RegexFindAllTest] = [
    # Lookahead matches at each position where the condition holds.
    RegexFindAllTest(
        "zero_width_lookahead",
        input="aba",
        regex="(?=a)",
        expected=[
            {"match": "", "idx": 0, "captures": []},
            {"match": "", "idx": 2, "captures": []},
        ],
        msg="$regexFindAll should produce zero-width matches at each lookahead position",
    ),
    # Engine advances by one code point after each zero-width match.
    RegexFindAllTest(
        "zero_width_advance_one_cp",
        input="abc",
        regex="(?=.)",
        expected=[
            {"match": "", "idx": 0, "captures": []},
            {"match": "", "idx": 1, "captures": []},
            {"match": "", "idx": 2, "captures": []},
        ],
        msg="$regexFindAll should advance one code point after each zero-width match",
    ),
    # Capturing lookahead: match is empty, captures populated from the lookahead content.
    RegexFindAllTest(
        "zero_width_capturing_lookahead",
        input="hello",
        regex="(?=(ll))",
        expected=[{"match": "", "idx": 2, "captures": ["ll"]}],
        msg="$regexFindAll capturing lookahead should have empty match but populated captures",
    ),
]

# Property [Empty Regex Matches]: an empty capturing group on non-empty input produces N matches
# (consistent with empty string regex behavior, not N+1).
REGEXFINDALL_EMPTY_REGEX_TESTS: list[RegexFindAllTest] = [
    RegexFindAllTest(
        "empty_regex_capturing_group",
        input="abc",
        regex="()",
        expected=[
            {"match": "", "idx": 0, "captures": [""]},
            {"match": "", "idx": 1, "captures": [""]},
            {"match": "", "idx": 2, "captures": [""]},
        ],
        msg="$regexFindAll empty capturing group should match at each code point position",
    ),
]

REGEXFINDALL_MATCHING_ALL_TESTS = (
    REGEXFINDALL_CAPTURES_TESTS
    + REGEXFINDALL_EDGE_TESTS
    + REGEXFINDALL_MULTI_MATCH_TESTS
    + REGEXFINDALL_ZERO_WIDTH_TESTS
    + REGEXFINDALL_EMPTY_REGEX_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(REGEXFINDALL_MATCHING_ALL_TESTS))
def test_regexfindall_matching(collection, test_case: RegexFindAllTest):
    """Test $regexFindAll matching behavior."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
