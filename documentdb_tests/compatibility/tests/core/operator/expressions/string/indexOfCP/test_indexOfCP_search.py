from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

from .utils.indexOfCP_common import (
    IndexOfCPTest,
)

# Property [First Occurrence]: when the substring appears multiple times, the result is the code
# point index of the first occurrence.
INDEXOFCP_FIRST_OCCURRENCE_TESTS: list[IndexOfCPTest] = [
    IndexOfCPTest(
        "first_occ_from_start",
        args=["abcabc", "abc"],
        expected=0,
        msg="$indexOfCP should find first occurrence at start",
    ),
    IndexOfCPTest(
        "first_occ_start_skips_first",
        args=["abcabc", "abc", 1],
        expected=3,
        msg="$indexOfCP should find second occurrence when start skips first",
    ),
    IndexOfCPTest(
        "first_occ_repeated_char",
        args=["aaaa", "a"],
        expected=0,
        msg="$indexOfCP should find first of repeated single characters",
    ),
    IndexOfCPTest(
        "first_occ_repeated_char_with_start",
        args=["aaaa", "a", 2],
        expected=2,
        msg="$indexOfCP should find first occurrence at start offset in repeated chars",
    ),
    IndexOfCPTest(
        "first_occ_with_end",
        args=["abcabc", "abc", 0, 6],
        expected=0,
        msg="$indexOfCP should find first occurrence within end boundary",
    ),
    IndexOfCPTest(
        "first_occ_start_and_end",
        args=["abcabc", "abc", 1, 6],
        expected=3,
        msg="$indexOfCP should find occurrence within start and end range",
    ),
]


# Property [Empty Substring]: empty substring behavior depends on start relative to string code
# point length.
INDEXOFCP_EMPTY_SUBSTRING_TESTS: list[IndexOfCPTest] = [
    IndexOfCPTest(
        "empty_sub_empty_string",
        args=["", ""],
        expected=0,
        msg="$indexOfCP should return 0 for empty substring in empty string",
    ),
    IndexOfCPTest(
        "empty_sub_non_empty_string",
        args=["hello", ""],
        expected=0,
        msg="$indexOfCP should return 0 for empty substring in non-empty string",
    ),
    IndexOfCPTest(
        "empty_sub_with_start_at_middle_cp",
        args=["hello", "", 3],
        expected=3,
        msg="$indexOfCP should return start for empty substring at middle code point",
    ),
    IndexOfCPTest(
        "empty_sub_start_at_last_cp",
        args=["hello", "", 4],
        expected=4,
        msg="$indexOfCP should return start for empty substring at last code point",
    ),
    # For $indexOfCP, start >= code point length returns -1 (unlike $indexOfBytes which returns
    # start when start == byte length).
    IndexOfCPTest(
        "empty_sub_start_at_cp_length",
        args=["hello", "", 5],
        expected=-1,
        msg="$indexOfCP should return -1 for empty substring at code point length",
    ),
    IndexOfCPTest(
        "empty_sub_start_beyond_cp_length",
        args=["hello", "", 6],
        expected=-1,
        msg="$indexOfCP should return -1 for empty substring beyond code point length",
    ),
    # Multi-byte string: "café" is 4 code points (é is 1 code point).
    IndexOfCPTest(
        "empty_sub_multibyte_start_at_cp_length",
        args=["café", "", 4],
        expected=-1,
        msg="$indexOfCP should return -1 for empty substring at multi-byte string cp length",
    ),
    IndexOfCPTest(
        "empty_sub_multibyte_start_beyond_cp_length",
        args=["café", "", 5],
        expected=-1,
        msg="$indexOfCP should return -1 for empty substring beyond multi-byte string cp length",
    ),
    # Empty search range: start == end returns -1 regardless of position, start > end also returns
    # -1.
    IndexOfCPTest(
        "empty_sub_edge_start_eq_end_zero",
        args=["hello", "", 0, 0],
        expected=-1,
        msg="$indexOfCP should return -1 for empty substring with start=end=0",
    ),
    IndexOfCPTest(
        "empty_sub_edge_start_eq_end_mid",
        args=["hello", "", 2, 2],
        expected=-1,
        msg="$indexOfCP should return -1 for empty substring with start=end mid-string",
    ),
    # start == end == cp_length also returns -1.
    IndexOfCPTest(
        "empty_sub_edge_start_eq_end_at_len",
        args=["hello", "", 5, 5],
        expected=-1,
        msg="$indexOfCP should return -1 for empty substring with start=end at cp length",
    ),
    IndexOfCPTest(
        "empty_sub_edge_start_gt_end",
        args=["hello", "", 3, 1],
        expected=-1,
        msg="$indexOfCP should return -1 for empty substring when start > end",
    ),
    IndexOfCPTest(
        "empty_sub_edge_start_gt_end_bounds",
        args=["hello", "", 5, 0],
        expected=-1,
        msg="$indexOfCP should return -1 for empty substring when start at length > end",
    ),
]


# Property [Start and End Range]: start and end constrain the code point range searched.
INDEXOFCP_RANGE_TESTS: list[IndexOfCPTest] = [
    # "lo" starts at code point 3, but end=3 means only code points 0-2 are searched.
    IndexOfCPTest(
        "range_end_excludes_match",
        args=["hello", "lo", 0, 3],
        expected=-1,
        msg="$indexOfCP should return -1 when end excludes the match position",
    ),
    IndexOfCPTest(
        "range_end_beyond_length",
        args=["hello", "lo", 0, 100],
        expected=3,
        msg="$indexOfCP should find match when end exceeds string length",
    ),
    IndexOfCPTest(
        "range_start_greater_than_end",
        args=["hello", "lo", 4, 2],
        expected=-1,
        msg="$indexOfCP should return -1 when start > end",
    ),
    IndexOfCPTest(
        "range_start_equals_end",
        args=["hello", "lo", 3, 3],
        expected=-1,
        msg="$indexOfCP should return -1 when start equals end",
    ),
    IndexOfCPTest(
        "range_start_at_cp_length",
        args=["hello", "lo", 5],
        expected=-1,
        msg="$indexOfCP should return -1 when start is at code point length",
    ),
    IndexOfCPTest(
        "range_start_at_last_cp",
        args=["hello", "o", 4],
        expected=4,
        msg="$indexOfCP should find single char at last code point position",
    ),
    IndexOfCPTest(
        "range_start_beyond_cp_length",
        args=["hello", "lo", 10],
        expected=-1,
        msg="$indexOfCP should return -1 when start is beyond code point length",
    ),
    # "llo" starts at code point 2. Unlike $indexOfBytes, $indexOfCP finds the match as long as it
    # starts within the range.
    IndexOfCPTest(
        "range_match_starts_within_end",
        args=["hello", "llo", 0, 4],
        expected=2,
        msg="$indexOfCP should find match that starts within end boundary",
    ),
    IndexOfCPTest(
        "range_match_fits_within_end",
        args=["hello", "llo", 0, 5],
        expected=2,
        msg="$indexOfCP should find match that fits within end boundary",
    ),
]


# Property [Overlapping Matches]: when overlapping matches exist, the result is the code point index
# of the first overlapping match.
INDEXOFCP_OVERLAPPING_TESTS: list[IndexOfCPTest] = [
    IndexOfCPTest(
        "overlap_ascii",
        args=["aaa", "aa"],
        expected=0,
        msg="$indexOfCP should return first overlapping match for ASCII",
    ),
    IndexOfCPTest(
        "overlap_2byte",
        args=["éééé", "éé"],
        expected=0,
        msg="$indexOfCP should return first overlapping match for 2-byte chars",
    ),
    IndexOfCPTest(
        "overlap_3byte",
        args=["中中中中", "中中"],
        expected=0,
        msg="$indexOfCP should return first overlapping match for 3-byte chars",
    ),
]


# Property [Edge Cases]: the operator handles boundary inputs correctly.
INDEXOFCP_EDGE_TESTS: list[IndexOfCPTest] = [
    IndexOfCPTest(
        "edge_empty_string",
        args=["", "hello"],
        expected=-1,
        msg="$indexOfCP should return -1 searching non-empty substring in empty string",
    ),
    IndexOfCPTest(
        "edge_at_end",
        args=["hello", "o"],
        expected=4,
        msg="$indexOfCP should find substring at end of string",
    ),
    IndexOfCPTest(
        "edge_equals_entire",
        args=["hello", "hello"],
        expected=0,
        msg="$indexOfCP should return 0 when substring equals entire string",
    ),
    IndexOfCPTest(
        "edge_longer_than_string",
        args=["hi", "hello"],
        expected=-1,
        msg="$indexOfCP should return -1 when substring is longer than string",
    ),
    # Number-like strings are treated as strings, not coerced to numeric types.
    IndexOfCPTest(
        "edge_number_like_zero",
        args=["a0b3", "0"],
        expected=1,
        msg="$indexOfCP should find '0' as a string, not coerce to number",
    ),
    IndexOfCPTest(
        "edge_number_like_digit",
        args=["a0b3", "3"],
        expected=3,
        msg="$indexOfCP should find '3' as a string, not coerce to number",
    ),
]

INDEXOFCP_SEARCH_TESTS = (
    INDEXOFCP_FIRST_OCCURRENCE_TESTS
    + INDEXOFCP_EMPTY_SUBSTRING_TESTS
    + INDEXOFCP_RANGE_TESTS
    + INDEXOFCP_OVERLAPPING_TESTS
    + INDEXOFCP_EDGE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(INDEXOFCP_SEARCH_TESTS))
def test_indexofcp_search(collection, test_case: IndexOfCPTest):
    """Test $indexOfCP search behavior."""
    result = execute_expression(collection, {"$indexOfCP": test_case.args})
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
