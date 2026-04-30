from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

from .utils.indexOfBytes_common import (
    IndexOfBytesTest,
)

# Property [First Occurrence]: when the substring appears multiple times, the result is the byte
# index of the first occurrence.
INDEXOFBYTES_FIRST_OCCURRENCE_TESTS: list[IndexOfBytesTest] = [
    IndexOfBytesTest(
        "first_occ_from_start",
        args=["abcabc", "abc"],
        expected=0,
        msg="$indexOfBytes should find first occurrence at start",
    ),
    IndexOfBytesTest(
        "first_occ_start_skips_first",
        args=["abcabc", "abc", 1],
        expected=3,
        msg="$indexOfBytes should find second occurrence when start skips first",
    ),
    IndexOfBytesTest(
        "first_occ_repeated_char",
        args=["aaaa", "a"],
        expected=0,
        msg="$indexOfBytes should find first of repeated single characters",
    ),
    IndexOfBytesTest(
        "first_occ_repeated_char_with_start",
        args=["aaaa", "a", 2],
        expected=2,
        msg="$indexOfBytes should find first occurrence at start offset in repeated chars",
    ),
    IndexOfBytesTest(
        "first_occ_with_end",
        args=["abcabc", "abc", 0, 6],
        expected=0,
        msg="$indexOfBytes should find first occurrence within end boundary",
    ),
    IndexOfBytesTest(
        "first_occ_start_and_end",
        args=["abcabc", "abc", 1, 6],
        expected=3,
        msg="$indexOfBytes should find occurrence within start and end range",
    ),
]

# Property [Empty Substring]: empty substring returns start when start <= byte_length, and -1 when
# start > byte_length, start > end, or start == end > byte_length.
INDEXOFBYTES_EMPTY_SUBSTRING_TESTS: list[IndexOfBytesTest] = [
    IndexOfBytesTest(
        "empty_sub_non_empty_string",
        args=["hello", ""],
        expected=0,
        msg="$indexOfBytes should return 0 for empty substring in non-empty string",
    ),
    IndexOfBytesTest(
        "empty_sub_with_start",
        args=["hello", "", 3],
        expected=3,
        msg="$indexOfBytes should return start for empty substring with start offset",
    ),
    IndexOfBytesTest(
        "empty_sub_empty_string",
        args=["", ""],
        expected=0,
        msg="$indexOfBytes should return 0 for empty substring in empty string",
    ),
    IndexOfBytesTest(
        "empty_sub_start_at_byte_length",
        args=["hello", "", 5],
        expected=5,
        msg="$indexOfBytes should return byte length for empty substring at end",
    ),
    IndexOfBytesTest(
        "empty_sub_start_beyond_byte_length",
        args=["hello", "", 6],
        expected=-1,
        msg="$indexOfBytes should return -1 for empty substring beyond byte length",
    ),
    # Multi-byte string: "café" is 5 bytes (é is 2 bytes).
    IndexOfBytesTest(
        "empty_sub_multibyte_start_at_byte_length",
        args=["café", "", 5],
        expected=5,
        msg="$indexOfBytes should return byte length for empty substr at end of multi-byte string",
    ),
    IndexOfBytesTest(
        "empty_sub_multibyte_start_beyond_byte_length",
        args=["café", "", 6],
        expected=-1,
        msg="$indexOfBytes should return -1 for empty substring beyond multi-byte string length",
    ),
    # Empty substring with start == end (empty range) returns start when start <= byte_length.
    IndexOfBytesTest(
        "empty_sub_start_eq_end_zero",
        args=["hello", "", 0, 0],
        expected=0,
        msg="$indexOfBytes should return 0 for empty substring with start=end=0",
    ),
    IndexOfBytesTest(
        "empty_sub_start_eq_end_mid",
        args=["hello", "", 3, 3],
        expected=3,
        msg="$indexOfBytes should return start for empty substring with start=end mid-string",
    ),
    IndexOfBytesTest(
        "empty_sub_start_eq_end_at_length",
        args=["hello", "", 5, 5],
        expected=5,
        msg="$indexOfBytes should return byte length for empty substring with start=end at length",
    ),
    IndexOfBytesTest(
        "empty_sub_start_eq_end_beyond_length",
        args=["hello", "", 6, 6],
        expected=-1,
        msg="$indexOfBytes should return -1 for empty substring with start=end beyond length",
    ),
    IndexOfBytesTest(
        "empty_sub_empty_str_start_eq_end_zero",
        args=["", "", 0, 0],
        expected=0,
        msg="$indexOfBytes should return 0 for empty substring in empty string with start=end=0",
    ),
    IndexOfBytesTest(
        "empty_sub_empty_str_start_eq_end_beyond",
        args=["", "", 1, 1],
        expected=-1,
        msg="$indexOfBytes should return -1 for empty substring in empty string with start=end=1",
    ),
    # Multi-byte: "café" is 5 bytes.
    IndexOfBytesTest(
        "empty_sub_multibyte_start_eq_end_at_length",
        args=["café", "", 5, 5],
        expected=5,
        msg="$indexOfBytes should return byte length for empty substr at start=end multi-byte end",
    ),
    IndexOfBytesTest(
        "empty_sub_multibyte_start_eq_end_beyond",
        args=["café", "", 6, 6],
        expected=-1,
        msg="$indexOfBytes should return -1 for empty substr with start=end beyond multi-byte end",
    ),
    # Empty substring where start > end returns -1.
    IndexOfBytesTest(
        "empty_sub_start_gt_end",
        args=["hello", "", 4, 2],
        expected=-1,
        msg="$indexOfBytes should return -1 for empty substring when start > end",
    ),
    IndexOfBytesTest(
        "empty_sub_start_gt_end_at_length",
        args=["hello", "", 5, 3],
        expected=-1,
        msg="$indexOfBytes should return -1 for empty substring when start at length > end",
    ),
    IndexOfBytesTest(
        "empty_sub_multibyte_start_gt_end",
        args=["café", "", 5, 3],
        expected=-1,
        msg="$indexOfBytes should return -1 for empty substr in multi-byte string when start > end",
    ),
]

# Property [Start and End Range]: start and end constrain the byte range searched.
INDEXOFBYTES_RANGE_TESTS: list[IndexOfBytesTest] = [
    # "lo" starts at byte 3, but end=3 means only bytes 0-2 are searched.
    IndexOfBytesTest(
        "range_end_excludes_match",
        args=["hello", "lo", 0, 3],
        expected=-1,
        msg="$indexOfBytes should return -1 when end excludes the match position",
    ),
    IndexOfBytesTest(
        "range_end_beyond_length",
        args=["hello", "lo", 0, 100],
        expected=3,
        msg="$indexOfBytes should find match when end exceeds string length",
    ),
    IndexOfBytesTest(
        "range_start_greater_than_end",
        args=["hello", "lo", 4, 2],
        expected=-1,
        msg="$indexOfBytes should return -1 when start > end",
    ),
    IndexOfBytesTest(
        "range_start_equals_end",
        args=["hello", "lo", 3, 3],
        expected=-1,
        msg="$indexOfBytes should return -1 when start equals end",
    ),
    IndexOfBytesTest(
        "range_start_at_byte_length",
        args=["hello", "lo", 5],
        expected=-1,
        msg="$indexOfBytes should return -1 when start is at byte length",
    ),
    IndexOfBytesTest(
        "range_start_at_last_byte",
        args=["hello", "o", 4],
        expected=4,
        msg="$indexOfBytes should find single char at last byte position",
    ),
    IndexOfBytesTest(
        "range_start_beyond_byte_length",
        args=["hello", "lo", 10],
        expected=-1,
        msg="$indexOfBytes should return -1 when start is beyond byte length",
    ),
    # "llo" at index 2 spans bytes 2-4, but end=4 excludes byte 4.
    IndexOfBytesTest(
        "range_match_extends_beyond_end",
        args=["hello", "llo", 0, 4],
        expected=-1,
        msg="$indexOfBytes should return -1 when match extends beyond end",
    ),
    IndexOfBytesTest(
        "range_match_fits_within_end",
        args=["hello", "llo", 0, 5],
        expected=2,
        msg="$indexOfBytes should find match that fits exactly within end",
    ),
]

# Property [Overlapping Matches]: when overlapping matches exist, the result is the byte index of
# the first overlapping match.
INDEXOFBYTES_OVERLAPPING_TESTS: list[IndexOfBytesTest] = [
    IndexOfBytesTest(
        "overlap_ascii",
        args=["aaa", "aa"],
        expected=0,
        msg="$indexOfBytes should return first overlapping match position for ASCII",
    ),
    # "éé" is 4 bytes; first match at byte 0 in "éééé" (8 bytes).
    IndexOfBytesTest(
        "overlap_2byte",
        args=["éééé", "éé"],
        expected=0,
        msg="$indexOfBytes should return first overlapping match for 2-byte chars",
    ),
    # "中中" is 6 bytes; first match at byte 0 in "中中中中" (12 bytes).
    IndexOfBytesTest(
        "overlap_3byte",
        args=["中中中中", "中中"],
        expected=0,
        msg="$indexOfBytes should return first overlapping match for 3-byte chars",
    ),
]

# Property [Edge Cases]: the operator handles boundary inputs correctly (empty strings, large
# strings, special characters).
INDEXOFBYTES_EDGE_TESTS: list[IndexOfBytesTest] = [
    IndexOfBytesTest(
        "edge_empty_string",
        args=["", "hello"],
        expected=-1,
        msg="$indexOfBytes should return -1 searching non-empty substring in empty string",
    ),
    IndexOfBytesTest(
        "edge_at_end",
        args=["hello", "o"],
        expected=4,
        msg="$indexOfBytes should find substring at end of string",
    ),
    IndexOfBytesTest(
        "edge_equals_entire",
        args=["hello", "hello"],
        expected=0,
        msg="$indexOfBytes should return 0 when substring equals entire string",
    ),
    IndexOfBytesTest(
        "edge_longer_than_string",
        args=["hi", "hello"],
        expected=-1,
        msg="$indexOfBytes should return -1 when substring is longer than string",
    ),
    # Number-like strings are treated as strings, not coerced to numeric types.
    IndexOfBytesTest(
        "edge_number_like_zero",
        args=["a0b3", "0"],
        expected=1,
        msg="$indexOfBytes should find '0' as a string, not coerce to number",
    ),
    IndexOfBytesTest(
        "edge_number_like_digit",
        args=["a0b3", "3"],
        expected=3,
        msg="$indexOfBytes should find '3' as a string, not coerce to number",
    ),
]


INDEXOFBYTES_SEARCH_TESTS = (
    INDEXOFBYTES_FIRST_OCCURRENCE_TESTS
    + INDEXOFBYTES_EMPTY_SUBSTRING_TESTS
    + INDEXOFBYTES_RANGE_TESTS
    + INDEXOFBYTES_OVERLAPPING_TESTS
    + INDEXOFBYTES_EDGE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(INDEXOFBYTES_SEARCH_TESTS))
def test_indexofbytes_cases(collection, test_case: IndexOfBytesTest):
    """Test $indexOfBytes cases."""
    result = execute_expression(collection, {"$indexOfBytes": test_case.args})
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
