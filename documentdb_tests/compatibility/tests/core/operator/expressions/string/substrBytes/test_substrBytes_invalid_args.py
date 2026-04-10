from __future__ import annotations

import pytest
from bson import (
    Decimal128,
    Int64,
)

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BSON_TO_STRING_CONVERSION_ERROR,
    EXPRESSION_TYPE_MISMATCH_ERROR,
    FAILED_TO_PARSE_ERROR,
    FIELD_PATH_NULL_BYTE_ERROR,
    INVALID_DOLLAR_FIELD_PATH,
    OUT_OF_RANGE_CONVERSION_ERROR,
    SUBSTR_CONTINUATION_BYTE_START_ERROR,
    SUBSTR_LENGTH_TYPE_ERROR,
    SUBSTR_MID_CHARACTER_END_ERROR,
    SUBSTR_NEGATIVE_START_ERROR,
    SUBSTR_START_TYPE_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_NEGATIVE_INFINITY,
    DOUBLE_NEAR_MAX,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT64_MIN,
)

from .utils.substrBytes_common import (
    OPERATORS,
    SubstrBytesTest,
    _expr,
)

# Property [Fractional Negative Boundary for Index - Error]: fractional values that round or
# truncate to -1 or below produce a negative start error. These are separated from
# SUBSTRBYTES_NEGATIVE_START_TESTS because they pair with the success-side fractional boundary
# tests that verify values just above the rounding threshold.
SUBSTRBYTES_FRAC_NEG_IDX_ERROR_TESTS: list[SubstrBytesTest] = [
    SubstrBytesTest(
        "frac_neg_idx_double_minus_1_0",
        string="hello",
        byte_index=-1.0,
        byte_count=3,
        error_code=SUBSTR_NEGATIVE_START_ERROR,
        msg="$substrBytes should reject double -1.0 as start index",
    ),
    SubstrBytesTest(
        "frac_neg_idx_decimal_minus_0_6",
        string="hello",
        byte_index=Decimal128("-0.6"),
        byte_count=3,
        error_code=SUBSTR_NEGATIVE_START_ERROR,
        msg="$substrBytes should reject Decimal128 -0.6 as start index (rounds to -1)",
    ),
]

# Property [Negative Start Error]: a negative byte_index value after numeric coercion produces an
# error, including Decimal128 special values that overflow to int64 min.
SUBSTRBYTES_NEGATIVE_START_TESTS: list[SubstrBytesTest] = [
    SubstrBytesTest(
        "neg_start_int32",
        string="hello",
        byte_index=-1,
        byte_count=3,
        error_code=SUBSTR_NEGATIVE_START_ERROR,
        msg="$substrBytes should reject negative int32 start",
    ),
    SubstrBytesTest(
        "neg_start_int32_large",
        string="hello",
        byte_index=-100,
        byte_count=3,
        error_code=SUBSTR_NEGATIVE_START_ERROR,
        msg="$substrBytes should reject large negative int32 start",
    ),
    SubstrBytesTest(
        "neg_start_int64",
        string="hello",
        byte_index=Int64(-1),
        byte_count=3,
        error_code=SUBSTR_NEGATIVE_START_ERROR,
        msg="$substrBytes should reject negative int64 start",
    ),
    SubstrBytesTest(
        "neg_start_int64_min",
        string="hello",
        byte_index=INT64_MIN,
        byte_count=3,
        error_code=SUBSTR_NEGATIVE_START_ERROR,
        msg="$substrBytes should reject INT64_MIN start",
    ),
    SubstrBytesTest(
        "neg_start_decimal_large",
        string="hello",
        byte_index=Decimal128("-100"),
        byte_count=3,
        error_code=SUBSTR_NEGATIVE_START_ERROR,
        msg="$substrBytes should reject large negative Decimal128 start",
    ),
    # Decimal128 special values overflow to int64 min, triggering negative start error.
    SubstrBytesTest(
        "neg_start_decimal_nan",
        string="hello",
        byte_index=Decimal128("NaN"),
        byte_count=3,
        error_code=SUBSTR_NEGATIVE_START_ERROR,
        msg="$substrBytes should reject Decimal128 NaN start as negative overflow",
    ),
    SubstrBytesTest(
        "neg_start_decimal_inf",
        string="hello",
        byte_index=DECIMAL128_INFINITY,
        byte_count=3,
        error_code=SUBSTR_NEGATIVE_START_ERROR,
        msg="$substrBytes should reject Decimal128 Infinity start as negative overflow",
    ),
    SubstrBytesTest(
        "neg_start_decimal_neg_inf",
        string="hello",
        byte_index=DECIMAL128_NEGATIVE_INFINITY,
        byte_count=3,
        error_code=SUBSTR_NEGATIVE_START_ERROR,
        msg="$substrBytes should reject Decimal128 -Infinity start as negative overflow",
    ),
    SubstrBytesTest(
        "neg_start_decimal_overflow",
        string="hello",
        byte_index=DECIMAL128_LARGE_EXPONENT,
        byte_count=3,
        error_code=SUBSTR_NEGATIVE_START_ERROR,
        msg="$substrBytes should reject Decimal128 1E+6144 start as negative overflow",
    ),
    SubstrBytesTest(
        "neg_start_decimal_max",
        string="hello",
        byte_index=Decimal128("9999999999999999999999999999999999E+6111"),
        byte_count=3,
        error_code=SUBSTR_NEGATIVE_START_ERROR,
        msg="$substrBytes should reject Decimal128 max value start as negative overflow",
    ),
    SubstrBytesTest(
        "neg_start_decimal_34_digit",
        string="hello",
        byte_index=Decimal128("9999999999999999999999999999999999"),
        byte_count=3,
        error_code=SUBSTR_NEGATIVE_START_ERROR,
        msg="$substrBytes should reject Decimal128 34-digit start as negative overflow",
    ),
]

# Property [Double Coercion Out-of-Range Error]: double NaN, infinity, negative infinity, and
# values outside int64 range cannot be coerced to long for either byte_index or byte_count.
SUBSTRBYTES_DOUBLE_COERCION_ERROR_TESTS: list[SubstrBytesTest] = [
    # byte_index.
    SubstrBytesTest(
        "double_coerce_start_nan",
        string="hello",
        byte_index=FLOAT_NAN,
        byte_count=3,
        error_code=OUT_OF_RANGE_CONVERSION_ERROR,
        msg="$substrBytes should reject double NaN start",
    ),
    SubstrBytesTest(
        "double_coerce_start_inf",
        string="hello",
        byte_index=FLOAT_INFINITY,
        byte_count=3,
        error_code=OUT_OF_RANGE_CONVERSION_ERROR,
        msg="$substrBytes should reject double Infinity start",
    ),
    SubstrBytesTest(
        "double_coerce_start_neg_inf",
        string="hello",
        byte_index=FLOAT_NEGATIVE_INFINITY,
        byte_count=3,
        error_code=OUT_OF_RANGE_CONVERSION_ERROR,
        msg="$substrBytes should reject double -Infinity start",
    ),
    SubstrBytesTest(
        "double_coerce_start_1e20",
        string="hello",
        byte_index=1e20,
        byte_count=3,
        error_code=OUT_OF_RANGE_CONVERSION_ERROR,
        msg="$substrBytes should reject double 1e20 start as out of range",
    ),
    SubstrBytesTest(
        "double_coerce_start_1e308",
        string="hello",
        byte_index=DOUBLE_NEAR_MAX,
        byte_count=3,
        error_code=OUT_OF_RANGE_CONVERSION_ERROR,
        msg="$substrBytes should reject near-max double start as out of range",
    ),
    # byte_count.
    SubstrBytesTest(
        "double_coerce_count_nan",
        string="hello",
        byte_index=0,
        byte_count=FLOAT_NAN,
        error_code=OUT_OF_RANGE_CONVERSION_ERROR,
        msg="$substrBytes should reject double NaN count",
    ),
    SubstrBytesTest(
        "double_coerce_count_inf",
        string="hello",
        byte_index=0,
        byte_count=FLOAT_INFINITY,
        error_code=OUT_OF_RANGE_CONVERSION_ERROR,
        msg="$substrBytes should reject double Infinity count",
    ),
    SubstrBytesTest(
        "double_coerce_count_neg_inf",
        string="hello",
        byte_index=0,
        byte_count=FLOAT_NEGATIVE_INFINITY,
        error_code=OUT_OF_RANGE_CONVERSION_ERROR,
        msg="$substrBytes should reject double -Infinity count",
    ),
    SubstrBytesTest(
        "double_coerce_count_1e20",
        string="hello",
        byte_index=0,
        byte_count=1e20,
        error_code=OUT_OF_RANGE_CONVERSION_ERROR,
        msg="$substrBytes should reject double 1e20 count as out of range",
    ),
    SubstrBytesTest(
        "double_coerce_count_1e308",
        string="hello",
        byte_index=0,
        byte_count=DOUBLE_NEAR_MAX,
        error_code=OUT_OF_RANGE_CONVERSION_ERROR,
        msg="$substrBytes should reject near-max double count as out of range",
    ),
]

# Property [UTF-8 Continuation Byte Start Error]: starting at a byte offset that is a UTF-8
# continuation byte produces an error, even with negative byte_count.
SUBSTRBYTES_CONTINUATION_START_TESTS: list[SubstrBytesTest] = [
    # 2-byte character é (U+00E9): continuation byte at offset 1.
    SubstrBytesTest(
        "cont_start_2byte_pos1",
        string="é",
        byte_index=1,
        byte_count=1,
        error_code=SUBSTR_CONTINUATION_BYTE_START_ERROR,
        msg="$substrBytes should reject start at continuation byte of 2-byte char",
    ),
    # 3-byte character 中 (U+4E2D): continuation bytes at offsets 1 and 2.
    SubstrBytesTest(
        "cont_start_3byte_pos1",
        string="中",
        byte_index=1,
        byte_count=1,
        error_code=SUBSTR_CONTINUATION_BYTE_START_ERROR,
        msg="$substrBytes should reject start at first continuation byte of 3-byte char",
    ),
    SubstrBytesTest(
        "cont_start_3byte_pos2",
        string="中",
        byte_index=2,
        byte_count=1,
        error_code=SUBSTR_CONTINUATION_BYTE_START_ERROR,
        msg="$substrBytes should reject start at second continuation byte of 3-byte char",
    ),
    # 4-byte character 😀 (U+1F600): continuation bytes at offsets 1, 2, and 3.
    SubstrBytesTest(
        "cont_start_4byte_pos1",
        string="😀",
        byte_index=1,
        byte_count=1,
        error_code=SUBSTR_CONTINUATION_BYTE_START_ERROR,
        msg="$substrBytes should reject start at first continuation byte of 4-byte char",
    ),
    SubstrBytesTest(
        "cont_start_4byte_pos2",
        string="😀",
        byte_index=2,
        byte_count=1,
        error_code=SUBSTR_CONTINUATION_BYTE_START_ERROR,
        msg="$substrBytes should reject start at second continuation byte of 4-byte char",
    ),
    SubstrBytesTest(
        "cont_start_4byte_pos3",
        string="😀",
        byte_index=3,
        byte_count=1,
        error_code=SUBSTR_CONTINUATION_BYTE_START_ERROR,
        msg="$substrBytes should reject start at third continuation byte of 4-byte char",
    ),
    # Combining mark U+0301 (2 bytes starting at offset 1 in "e\u0301").
    SubstrBytesTest(
        "cont_start_combining_mark",
        string="e\u0301",
        byte_index=2,
        byte_count=1,
        error_code=SUBSTR_CONTINUATION_BYTE_START_ERROR,
        msg="$substrBytes should reject start at continuation byte of combining mark",
    ),
    # BOM U+FEFF (3 bytes): continuation bytes at offsets 1 and 2.
    SubstrBytesTest(
        "cont_start_bom_pos1",
        string="\ufeff",
        byte_index=1,
        byte_count=1,
        error_code=SUBSTR_CONTINUATION_BYTE_START_ERROR,
        msg="$substrBytes should reject start at continuation byte of BOM",
    ),
    # ZWJ U+200D (3 bytes): continuation byte at offset 1.
    SubstrBytesTest(
        "cont_start_zwj_pos1",
        string="\u200d",
        byte_index=1,
        byte_count=1,
        error_code=SUBSTR_CONTINUATION_BYTE_START_ERROR,
        msg="$substrBytes should reject start at continuation byte of ZWJ",
    ),
    # Negative byte_count does not bypass the check.
    SubstrBytesTest(
        "cont_start_neg_count",
        string="é",
        byte_index=1,
        byte_count=-1,
        error_code=SUBSTR_CONTINUATION_BYTE_START_ERROR,
        msg="$substrBytes should reject continuation byte start even with negative count",
    ),
]

# Property [UTF-8 Mid-Character End Error]: when start + byte_count lands in the middle of a
# multi-byte UTF-8 character, an error is produced.
SUBSTRBYTES_MID_CHAR_END_TESTS: list[SubstrBytesTest] = [
    # 2-byte character é: byte_index=0, byte_count=1 lands mid-character.
    SubstrBytesTest(
        "mid_end_2byte_pos1",
        string="é",
        byte_index=0,
        byte_count=1,
        error_code=SUBSTR_MID_CHARACTER_END_ERROR,
        msg="$substrBytes should reject length landing mid 2-byte character",
    ),
    # 3-byte character 中: byte_count=1 and byte_count=2 both land mid-character.
    SubstrBytesTest(
        "mid_end_3byte_pos1",
        string="中",
        byte_index=0,
        byte_count=1,
        error_code=SUBSTR_MID_CHARACTER_END_ERROR,
        msg="$substrBytes should reject length 1 landing mid 3-byte character",
    ),
    SubstrBytesTest(
        "mid_end_3byte_pos2",
        string="中",
        byte_index=0,
        byte_count=2,
        error_code=SUBSTR_MID_CHARACTER_END_ERROR,
        msg="$substrBytes should reject length 2 landing mid 3-byte character",
    ),
    # 4-byte character 😀: byte_count=1, 2, 3 all land mid-character.
    SubstrBytesTest(
        "mid_end_4byte_pos1",
        string="😀",
        byte_index=0,
        byte_count=1,
        error_code=SUBSTR_MID_CHARACTER_END_ERROR,
        msg="$substrBytes should reject length 1 landing mid 4-byte character",
    ),
    SubstrBytesTest(
        "mid_end_4byte_pos2",
        string="😀",
        byte_index=0,
        byte_count=2,
        error_code=SUBSTR_MID_CHARACTER_END_ERROR,
        msg="$substrBytes should reject length 2 landing mid 4-byte character",
    ),
    SubstrBytesTest(
        "mid_end_4byte_pos3",
        string="😀",
        byte_index=0,
        byte_count=3,
        error_code=SUBSTR_MID_CHARACTER_END_ERROR,
        msg="$substrBytes should reject length 3 landing mid 4-byte character",
    ),
    # Mixed string "café" = 3 ASCII + 2-byte é = 5 bytes. Length 4 lands mid-é.
    SubstrBytesTest(
        "mid_end_mixed_cafe",
        string="café",
        byte_index=0,
        byte_count=4,
        error_code=SUBSTR_MID_CHARACTER_END_ERROR,
        msg="$substrBytes should reject length landing mid-character in mixed string",
    ),
    # Fractional double truncation causes mid-character end: "café", double(4.5) truncates to 4.
    SubstrBytesTest(
        "mid_end_double_trunc",
        string="café",
        byte_index=0,
        byte_count=4.5,
        error_code=SUBSTR_MID_CHARACTER_END_ERROR,
        msg="$substrBytes should reject truncated double length landing mid-character",
    ),
    # Decimal128 rounding causes mid-character end: "café", Decimal128("3.5") rounds to 4.
    SubstrBytesTest(
        "mid_end_decimal_round",
        string="café",
        byte_index=0,
        byte_count=Decimal128("3.5"),
        error_code=SUBSTR_MID_CHARACTER_END_ERROR,
        msg="$substrBytes should reject rounded Decimal128 length landing mid-character",
    ),
]


# Property [Error Precedence]: errors are evaluated in priority order: string type before index
# type before count type before double coercion before negative start before mid-char start before
# mid-char end.
SUBSTRBYTES_PRECEDENCE_TESTS: list[SubstrBytesTest] = [
    # String type error takes precedence over index type error.
    SubstrBytesTest(
        "prec_string_over_index",
        string=True,
        byte_index="bad",
        byte_count=3,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$substrBytes string type error should precede index type error",
    ),
    # String type error takes precedence over count type error.
    SubstrBytesTest(
        "prec_string_over_count",
        string=True,
        byte_index=0,
        byte_count="bad",
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$substrBytes string type error should precede count type error",
    ),
    # String type error takes precedence when all three params are invalid.
    SubstrBytesTest(
        "prec_string_over_all",
        string=True,
        byte_index="bad",
        byte_count="bad",
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$substrBytes string type error should precede all other errors",
    ),
    # Index type error takes precedence over count type error.
    SubstrBytesTest(
        "prec_index_over_count",
        string="hello",
        byte_index="bad",
        byte_count="bad",
        error_code=SUBSTR_START_TYPE_ERROR,
        msg="$substrBytes index type error should precede count type error",
    ),
    # Index type error (null) takes precedence over negative count behavior.
    SubstrBytesTest(
        "prec_index_null_over_neg_count",
        string="hello",
        byte_index=None,
        byte_count=-1,
        error_code=SUBSTR_START_TYPE_ERROR,
        msg="$substrBytes null index error should precede negative count behavior",
    ),
    # Count type error (null) takes precedence over negative start error.
    SubstrBytesTest(
        "prec_count_null_over_neg_start",
        string="hello",
        byte_index=-1,
        byte_count=None,
        error_code=SUBSTR_LENGTH_TYPE_ERROR,
        msg="$substrBytes null count error should precede negative start error",
    ),
    # Double coercion error takes precedence over negative start.
    SubstrBytesTest(
        "prec_double_coerce_over_neg_start",
        string="hello",
        byte_index=FLOAT_NAN,
        byte_count=-1,
        error_code=OUT_OF_RANGE_CONVERSION_ERROR,
        msg="$substrBytes double coercion error should precede negative start error",
    ),
    # Negative start error takes precedence over mid-char start.
    SubstrBytesTest(
        "prec_neg_start_over_cont_start",
        string="é",
        byte_index=-1,
        byte_count=1,
        error_code=SUBSTR_NEGATIVE_START_ERROR,
        msg="$substrBytes negative start error should precede continuation byte error",
    ),
    # Mid-char start error takes precedence over mid-char end.
    SubstrBytesTest(
        "prec_cont_start_over_mid_end",
        string="éé",
        byte_index=1,
        byte_count=1,
        error_code=SUBSTR_CONTINUATION_BYTE_START_ERROR,
        msg="$substrBytes continuation byte error should precede mid-character end error",
    ),
    # Null-string-returns-empty only applies when index and count are valid. Count type error fires
    # even when string is null.
    SubstrBytesTest(
        "prec_count_type_over_null_string",
        string=None,
        byte_index=0,
        byte_count="bad",
        error_code=SUBSTR_LENGTH_TYPE_ERROR,
        msg="$substrBytes count type error should fire even when string is null",
    ),
    # Index type error fires even when string is null.
    SubstrBytesTest(
        "prec_index_type_over_null_string",
        string=None,
        byte_index="bad",
        byte_count=3,
        error_code=SUBSTR_START_TYPE_ERROR,
        msg="$substrBytes index type error should fire even when string is null",
    ),
]

# Property [Arity Errors]: $substrBytes requires exactly 3 arguments in an array; fewer, more, or
# non-array shapes produce an error.
SUBSTRBYTES_ARITY_ERROR_TESTS: list[SubstrBytesTest] = [
    SubstrBytesTest(
        "arity_zero_args",
        raw_args=[],
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$substrBytes should reject empty array",
    ),
    SubstrBytesTest(
        "arity_one_arg",
        raw_args=["hello"],
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$substrBytes should reject single-element array",
    ),
    SubstrBytesTest(
        "arity_two_args",
        raw_args=["hello", 0],
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$substrBytes should reject two-element array",
    ),
    SubstrBytesTest(
        "arity_four_args",
        raw_args=["hello", 0, 5, 1],
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$substrBytes should reject four-element array",
    ),
    SubstrBytesTest(
        "arity_bare_string",
        raw_args="hello",
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$substrBytes should reject bare string argument",
    ),
    SubstrBytesTest(
        "arity_bare_object",
        raw_args={"a": 1},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$substrBytes should reject bare object argument",
    ),
    SubstrBytesTest(
        "arity_bare_number",
        raw_args=42,
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$substrBytes should reject bare number argument",
    ),
    SubstrBytesTest(
        "arity_bare_null",
        raw_args=None,
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$substrBytes should reject bare null argument",
    ),
]

# Property [Field Path Parsing]: bare "$", "$$", and null-byte field paths produce parse-time
# errors in each parameter position.
SUBSTRBYTES_FIELD_PATH_ERROR_TESTS: list[SubstrBytesTest] = [
    SubstrBytesTest(
        "fieldpath_bare_dollar_string",
        string="$",
        byte_index=0,
        byte_count=1,
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$substrBytes should reject bare '$' as string parameter",
    ),
    SubstrBytesTest(
        "fieldpath_double_dollar_string",
        string="$$",
        byte_index=0,
        byte_count=1,
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$substrBytes should reject '$$' as string parameter",
    ),
    SubstrBytesTest(
        "fieldpath_null_byte_string",
        string="$a\x00b",
        byte_index=0,
        byte_count=1,
        error_code=FIELD_PATH_NULL_BYTE_ERROR,
        msg="$substrBytes should reject field path with null byte as string parameter",
    ),
    SubstrBytesTest(
        "fieldpath_bare_dollar_index",
        string="hello",
        byte_index="$",
        byte_count=1,
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$substrBytes should reject bare '$' as byte_index",
    ),
    SubstrBytesTest(
        "fieldpath_double_dollar_index",
        string="hello",
        byte_index="$$",
        byte_count=1,
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$substrBytes should reject '$$' as byte_index",
    ),
    SubstrBytesTest(
        "fieldpath_null_byte_index",
        string="hello",
        byte_index="$a\x00b",
        byte_count=1,
        error_code=FIELD_PATH_NULL_BYTE_ERROR,
        msg="$substrBytes should reject field path with null byte as byte_index",
    ),
    SubstrBytesTest(
        "fieldpath_bare_dollar_count",
        string="hello",
        byte_index=0,
        byte_count="$",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$substrBytes should reject bare '$' as byte_count",
    ),
    SubstrBytesTest(
        "fieldpath_double_dollar_count",
        string="hello",
        byte_index=0,
        byte_count="$$",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$substrBytes should reject '$$' as byte_count",
    ),
    SubstrBytesTest(
        "fieldpath_null_byte_count",
        string="hello",
        byte_index=0,
        byte_count="$a\x00b",
        error_code=FIELD_PATH_NULL_BYTE_ERROR,
        msg="$substrBytes should reject field path with null byte as byte_count",
    ),
]


SUBSTRBYTES_INVALID_ARGS_ALL_TESTS = (
    SUBSTRBYTES_FRAC_NEG_IDX_ERROR_TESTS
    + SUBSTRBYTES_NEGATIVE_START_TESTS
    + SUBSTRBYTES_DOUBLE_COERCION_ERROR_TESTS
    + SUBSTRBYTES_CONTINUATION_START_TESTS
    + SUBSTRBYTES_MID_CHAR_END_TESTS
    + SUBSTRBYTES_PRECEDENCE_TESTS
    + SUBSTRBYTES_ARITY_ERROR_TESTS
    + SUBSTRBYTES_FIELD_PATH_ERROR_TESTS
)


@pytest.mark.parametrize("op", OPERATORS)
@pytest.mark.parametrize("test_case", pytest_params(SUBSTRBYTES_INVALID_ARGS_ALL_TESTS))
def test_substrbytes_invalid_args(collection, op, test_case: SubstrBytesTest):
    """Test $substrBytes cases."""
    result = execute_expression(collection, _expr(test_case, op))
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
