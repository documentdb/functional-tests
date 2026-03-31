from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.framework.test_constants import (
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.string.substrBytes.utils.substrBytes_common import (
    OPERATORS,
    SubstrBytesTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import execute_expression

# Property [Core Substring Extraction]: $substrBytes operates on zero-based UTF-8 byte positions and
# returns the substring starting at the given byte index for the specified number of bytes.
SUBSTRBYTES_CORE_TESTS: list[SubstrBytesTest] = [
    SubstrBytesTest(
        "core_full_string",
        string="hello",
        byte_index=0,
        byte_count=5,
        expected="hello",
        msg="$substrBytes should extract full string",
    ),
    SubstrBytesTest(
        "core_first_byte",
        string="hello",
        byte_index=0,
        byte_count=1,
        expected="h",
        msg="$substrBytes should extract first byte",
    ),
    SubstrBytesTest(
        "core_last_byte",
        string="hello",
        byte_index=4,
        byte_count=1,
        expected="o",
        msg="$substrBytes should extract last byte",
    ),
    SubstrBytesTest(
        "core_middle",
        string="hello",
        byte_index=1,
        byte_count=3,
        expected="ell",
        msg="$substrBytes should extract middle bytes",
    ),
    SubstrBytesTest(
        "core_offset_two",
        string="hello",
        byte_index=2,
        byte_count=2,
        expected="ll",
        msg="$substrBytes should extract from offset two",
    ),
    SubstrBytesTest(
        "core_ten_chars",
        string="abcdefghij",
        byte_index=0,
        byte_count=10,
        expected="abcdefghij",
        msg="$substrBytes should extract ten characters",
    ),
    SubstrBytesTest(
        "core_second_half",
        string="abcdefghij",
        byte_index=5,
        byte_count=5,
        expected="fghij",
        msg="$substrBytes should extract second half",
    ),
    SubstrBytesTest(
        "core_inner_slice",
        string="abcdefghij",
        byte_index=3,
        byte_count=4,
        expected="defg",
        msg="$substrBytes should extract inner slice",
    ),
    SubstrBytesTest(
        "core_single_char",
        string="a",
        byte_index=0,
        byte_count=1,
        expected="a",
        msg="$substrBytes should extract single character",
    ),
]


# Property [Negative Length]: any negative byte_count value returns the rest of the string from the
# start position to the end, regardless of the magnitude of the negative value.
SUBSTRBYTES_NEGATIVE_LENGTH_TESTS: list[SubstrBytesTest] = [
    SubstrBytesTest(
        "neg_len_minus_one",
        string="hello",
        byte_index=0,
        byte_count=-1,
        expected="hello",
        msg="$substrBytes should return rest of string for length -1",
    ),
    SubstrBytesTest(
        "neg_len_minus_100",
        string="hello",
        byte_index=0,
        byte_count=-100,
        expected="hello",
        msg="$substrBytes should return rest of string for length -100",
    ),
    SubstrBytesTest(
        "neg_len_int32_min",
        string="hello",
        byte_index=0,
        byte_count=INT32_MIN,
        expected="hello",
        msg="$substrBytes should return rest of string for INT32_MIN length",
    ),
    SubstrBytesTest(
        "neg_len_int64_min",
        string="hello",
        byte_index=0,
        byte_count=INT64_MIN,
        expected="hello",
        msg="$substrBytes should return rest of string for INT64_MIN length",
    ),
    SubstrBytesTest(
        "neg_len_from_middle",
        string="hello",
        byte_index=2,
        byte_count=-1,
        expected="llo",
        msg="$substrBytes should return rest from middle with negative length",
    ),
    SubstrBytesTest(
        "neg_len_from_last",
        string="hello",
        byte_index=4,
        byte_count=-1,
        expected="o",
        msg="$substrBytes should return last byte with negative length",
    ),
    SubstrBytesTest(
        "neg_len_at_end",
        string="hello",
        byte_index=5,
        byte_count=-1,
        expected="",
        msg="$substrBytes should return empty string at end with negative length",
    ),
    SubstrBytesTest(
        "neg_len_beyond_end",
        string="hello",
        byte_index=10,
        byte_count=-1,
        expected="",
        msg="$substrBytes should return empty string beyond end with negative length",
    ),
    SubstrBytesTest(
        "neg_len_empty_string",
        string="",
        byte_index=0,
        byte_count=-1,
        expected="",
        msg="$substrBytes should return empty string for empty input with negative length",
    ),
    # Multi-byte string with negative length returns full string (no mid-character end error).
    SubstrBytesTest(
        "neg_len_multibyte",
        string="aé中😀",
        byte_index=0,
        byte_count=-1,
        expected="aé中😀",
        msg="$substrBytes should return full multi-byte string with negative length",
    ),
]


# Property [Boundary Behavior]: start index at or beyond the string byte length returns empty
# string, byte count exceeding remaining bytes clamps to the end, and empty or very large strings
# are handled correctly at all positions.
SUBSTRBYTES_BOUNDARY_TESTS: list[SubstrBytesTest] = [
    # Start at exactly the string byte length.
    SubstrBytesTest(
        "boundary_start_at_end",
        string="hello",
        byte_index=5,
        byte_count=1,
        expected="",
        msg="$substrBytes should return empty when start equals string length",
    ),
    # Start beyond the string byte length.
    SubstrBytesTest(
        "boundary_start_beyond",
        string="hello",
        byte_index=6,
        byte_count=1,
        expected="",
        msg="$substrBytes should return empty when start exceeds string length",
    ),
    SubstrBytesTest(
        "boundary_start_int32_max",
        string="hello",
        byte_index=INT32_MAX,
        byte_count=1,
        expected="",
        msg="$substrBytes should return empty for INT32_MAX start",
    ),
    SubstrBytesTest(
        "boundary_start_int64_max",
        string="hello",
        byte_index=INT64_MAX,
        byte_count=1,
        expected="",
        msg="$substrBytes should return empty for INT64_MAX start",
    ),
    # Byte count exceeding remaining bytes clamps to end.
    SubstrBytesTest(
        "boundary_count_exceeds",
        string="hello",
        byte_index=0,
        byte_count=100,
        expected="hello",
        msg="$substrBytes should clamp count exceeding string length",
    ),
    SubstrBytesTest(
        "boundary_count_exceeds_mid",
        string="hello",
        byte_index=3,
        byte_count=100,
        expected="lo",
        msg="$substrBytes should clamp count exceeding remaining bytes from middle",
    ),
    # Multi-byte string with count exceeding byte length clamps to end.
    SubstrBytesTest(
        "boundary_count_exceeds_multibyte",
        string="aé中😀",
        byte_index=0,
        byte_count=100,
        expected="aé中😀",
        msg="$substrBytes should clamp count exceeding multi-byte string length",
    ),
    # int32 max and int64 max accepted as byte_count.
    SubstrBytesTest(
        "boundary_count_int32_max",
        string="hello",
        byte_index=0,
        byte_count=INT32_MAX,
        expected="hello",
        msg="$substrBytes should accept INT32_MAX as byte count",
    ),
    SubstrBytesTest(
        "boundary_count_int64_max",
        string="hello",
        byte_index=0,
        byte_count=INT64_MAX,
        expected="hello",
        msg="$substrBytes should accept INT64_MAX as byte count",
    ),
    # Zero byte count at various positions.
    SubstrBytesTest(
        "boundary_zero_count_start",
        string="hello",
        byte_index=0,
        byte_count=0,
        expected="",
        msg="$substrBytes should return empty for zero count at start",
    ),
    SubstrBytesTest(
        "boundary_zero_count_mid",
        string="hello",
        byte_index=3,
        byte_count=0,
        expected="",
        msg="$substrBytes should return empty for zero count at middle",
    ),
    SubstrBytesTest(
        "boundary_zero_count_at_end",
        string="hello",
        byte_index=5,
        byte_count=0,
        expected="",
        msg="$substrBytes should return empty for zero count at end",
    ),
    # Empty string with various parameters.
    SubstrBytesTest(
        "boundary_empty_zero_zero",
        string="",
        byte_index=0,
        byte_count=0,
        expected="",
        msg="$substrBytes should return empty for empty string with zero params",
    ),
    SubstrBytesTest(
        "boundary_empty_positive_len",
        string="",
        byte_index=0,
        byte_count=5,
        expected="",
        msg="$substrBytes should return empty for empty string with positive length",
    ),
    SubstrBytesTest(
        "boundary_empty_beyond_start",
        string="",
        byte_index=5,
        byte_count=5,
        expected="",
        msg="$substrBytes should return empty for empty string with start beyond length",
    ),
    # Large start + large count whose sum would overflow int64 produces no error.
    SubstrBytesTest(
        "boundary_overflow_start_count_sum",
        string="hello",
        byte_index=INT64_MAX,
        byte_count=INT64_MAX,
        expected="",
        msg="$substrBytes should handle INT64_MAX start and count without overflow error",
    ),
    SubstrBytesTest(
        "boundary_overflow_int32_max_start_int64_max_count",
        string="hello",
        byte_index=INT32_MAX,
        byte_count=INT64_MAX,
        expected="",
        msg="$substrBytes should handle INT32_MAX start and INT64_MAX count without overflow error",
    ),
]


SUBSTRBYTES_CORE_ALL_TESTS = (
    SUBSTRBYTES_CORE_TESTS + SUBSTRBYTES_NEGATIVE_LENGTH_TESTS + SUBSTRBYTES_BOUNDARY_TESTS
)


@pytest.mark.parametrize("op", OPERATORS)
@pytest.mark.parametrize("test_case", pytest_params(SUBSTRBYTES_CORE_ALL_TESTS))
def test_substrbytes_core(collection, op, test_case: SubstrBytesTest):
    """Test $substrBytes cases."""
    result = execute_expression(collection, _expr(test_case, op))
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
