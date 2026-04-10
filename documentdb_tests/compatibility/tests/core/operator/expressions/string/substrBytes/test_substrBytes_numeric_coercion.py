from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_HALF,
    DECIMAL128_INFINITY,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_NEGATIVE_HALF,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ONE_AND_HALF,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_SMALL_EXPONENT,
    DECIMAL128_TWO_AND_HALF,
    DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEGATIVE_ZERO,
)

from .utils.substrBytes_common import (
    OPERATORS,
    SubstrBytesTest,
    _expr,
)

# Property [Numeric Coercion for Index and Count]: int32, int64, double, and Decimal128 are all
# accepted for byte_index and byte_count, with fractional doubles truncated toward zero and
# fractional Decimal128 values rounded using banker's rounding (round half to even).
SUBSTRBYTES_NUMERIC_COERCION_TESTS: list[SubstrBytesTest] = [
    # Each numeric type accepted for both parameters.
    SubstrBytesTest(
        "coerce_idx_int64",
        string="hello",
        byte_index=Int64(1),
        byte_count=Int64(3),
        expected="ell",
        msg="$substrBytes should accept int64 for both parameters",
    ),
    SubstrBytesTest(
        "coerce_idx_double",
        string="hello",
        byte_index=1.0,
        byte_count=3.0,
        expected="ell",
        msg="$substrBytes should accept double for both parameters",
    ),
    SubstrBytesTest(
        "coerce_idx_decimal",
        string="hello",
        byte_index=Decimal128("1"),
        byte_count=Decimal128("3"),
        expected="ell",
        msg="$substrBytes should accept Decimal128 for both parameters",
    ),
    # Mixed numeric types across parameters.
    SubstrBytesTest(
        "coerce_mixed_int32_decimal",
        string="hello",
        byte_index=1,
        byte_count=Decimal128("3"),
        expected="ell",
        msg="$substrBytes should accept mixed int32 start and Decimal128 length",
    ),
    SubstrBytesTest(
        "coerce_mixed_int64_double",
        string="hello",
        byte_index=Int64(1),
        byte_count=2.0,
        expected="el",
        msg="$substrBytes should accept mixed int64 start and double length",
    ),
    SubstrBytesTest(
        "coerce_mixed_double_int64",
        string="hello",
        byte_index=1.0,
        byte_count=Int64(3),
        expected="ell",
        msg="$substrBytes should accept mixed double start and int64 length",
    ),
    SubstrBytesTest(
        "coerce_mixed_decimal_int32",
        string="hello",
        byte_index=Decimal128("1"),
        byte_count=3,
        expected="ell",
        msg="$substrBytes should accept mixed Decimal128 start and int32 length",
    ),
    # Fractional double truncated toward zero (C-style cast).
    SubstrBytesTest(
        "coerce_double_trunc_start",
        string="hello",
        byte_index=1.9,
        byte_count=3,
        expected="ell",
        msg="$substrBytes should truncate fractional double start toward zero",
    ),
    SubstrBytesTest(
        "coerce_double_trunc_start_half",
        string="hello",
        byte_index=0.5,
        byte_count=5,
        expected="hello",
        msg="$substrBytes should truncate 0.5 start to 0",
    ),
    SubstrBytesTest(
        "coerce_double_trunc_length",
        string="hello",
        byte_index=0,
        byte_count=1.9,
        expected="h",
        msg="$substrBytes should truncate fractional double length toward zero",
    ),
    SubstrBytesTest(
        "coerce_double_trunc_length_half",
        string="hello",
        byte_index=0,
        byte_count=0.5,
        expected="",
        msg="$substrBytes should truncate 0.5 length to 0",
    ),
    # Fractional Decimal128 uses banker's rounding (round half to even).
    SubstrBytesTest(
        "coerce_decimal_round_start_0_5",
        string="hello",
        byte_index=DECIMAL128_HALF,
        byte_count=5,
        expected="hello",
        msg="$substrBytes should round Decimal128 0.5 start to 0 (even)",
    ),
    SubstrBytesTest(
        "coerce_decimal_round_start_1_5",
        string="hello",
        byte_index=DECIMAL128_ONE_AND_HALF,
        byte_count=3,
        expected="llo",
        msg="$substrBytes should round Decimal128 1.5 start to 2 (even)",
    ),
    SubstrBytesTest(
        "coerce_decimal_round_start_2_5",
        string="hello",
        byte_index=DECIMAL128_TWO_AND_HALF,
        byte_count=3,
        expected="llo",
        msg="$substrBytes should round Decimal128 2.5 start to 2 (even)",
    ),
    SubstrBytesTest(
        "coerce_decimal_round_length_0_5",
        string="hello",
        byte_index=0,
        byte_count=DECIMAL128_HALF,
        expected="",
        msg="$substrBytes should round Decimal128 0.5 length to 0 (even)",
    ),
    SubstrBytesTest(
        "coerce_decimal_round_length_1_5",
        string="hello",
        byte_index=0,
        byte_count=DECIMAL128_ONE_AND_HALF,
        expected="he",
        msg="$substrBytes should round Decimal128 1.5 length to 2 (even)",
    ),
    SubstrBytesTest(
        "coerce_decimal_round_length_2_5",
        string="hello",
        byte_index=0,
        byte_count=DECIMAL128_TWO_AND_HALF,
        expected="he",
        msg="$substrBytes should round Decimal128 2.5 length to 2 (even)",
    ),
    # Double -0.0 treated as 0.
    SubstrBytesTest(
        "coerce_double_neg_zero_start",
        string="hello",
        byte_index=DOUBLE_NEGATIVE_ZERO,
        byte_count=3,
        expected="hel",
        msg="$substrBytes should treat double -0.0 start as 0",
    ),
    SubstrBytesTest(
        "coerce_double_neg_zero_length",
        string="hello",
        byte_index=0,
        byte_count=DOUBLE_NEGATIVE_ZERO,
        expected="",
        msg="$substrBytes should treat double -0.0 length as 0",
    ),
    # Decimal128 "-0" treated as 0.
    SubstrBytesTest(
        "coerce_decimal_neg_zero_start",
        string="hello",
        byte_index=DECIMAL128_NEGATIVE_ZERO,
        byte_count=3,
        expected="hel",
        msg="$substrBytes should treat Decimal128 -0 start as 0",
    ),
    SubstrBytesTest(
        "coerce_decimal_neg_zero_length",
        string="hello",
        byte_index=0,
        byte_count=DECIMAL128_NEGATIVE_ZERO,
        expected="",
        msg="$substrBytes should treat Decimal128 -0 length as 0",
    ),
    # Decimal128 trailing zeros and scientific notation resolve correctly.
    SubstrBytesTest(
        "coerce_decimal_trailing_zeros",
        string="hello",
        byte_index=Decimal128("3.00"),
        byte_count=2,
        expected="lo",
        msg="$substrBytes should resolve Decimal128 with trailing zeros",
    ),
    SubstrBytesTest(
        "coerce_decimal_sci_notation",
        string="hello",
        byte_index=Decimal128("3E0"),
        byte_count=2,
        expected="lo",
        msg="$substrBytes should resolve Decimal128 in scientific notation",
    ),
    SubstrBytesTest(
        "coerce_decimal_sci_neg_exp",
        string="hello",
        byte_index=Decimal128("30E-1"),
        byte_count=2,
        expected="lo",
        msg="$substrBytes should resolve Decimal128 with negative exponent",
    ),
    # Tiny Decimal128 rounds to 0.
    SubstrBytesTest(
        "coerce_decimal_tiny_start",
        string="hello",
        byte_index=DECIMAL128_SMALL_EXPONENT,
        byte_count=5,
        expected="hello",
        msg="$substrBytes should round tiny Decimal128 start to 0",
    ),
    SubstrBytesTest(
        "coerce_decimal_tiny_length",
        string="hello",
        byte_index=0,
        byte_count=DECIMAL128_SMALL_EXPONENT,
        expected="",
        msg="$substrBytes should round tiny Decimal128 length to 0",
    ),
    # Double min subnormal and negative min subnormal truncate to 0.
    SubstrBytesTest(
        "coerce_double_subnormal_start",
        string="hello",
        byte_index=DOUBLE_MIN_SUBNORMAL,
        byte_count=5,
        expected="hello",
        msg="$substrBytes should truncate subnormal double start to 0",
    ),
    SubstrBytesTest(
        "coerce_double_neg_subnormal_start",
        string="hello",
        byte_index=DOUBLE_MIN_NEGATIVE_SUBNORMAL,
        byte_count=5,
        expected="hello",
        msg="$substrBytes should truncate negative subnormal double start to 0",
    ),
    SubstrBytesTest(
        "coerce_double_subnormal_length",
        string="hello",
        byte_index=0,
        byte_count=DOUBLE_MIN_SUBNORMAL,
        expected="",
        msg="$substrBytes should truncate subnormal double length to 0",
    ),
]

# Property [Fractional Negative Boundary for Index - Success]: fractional doubles between -1
# exclusive and 0 exclusive truncate to 0 and succeed as byte_index, and Decimal128 "-0.5" rounds
# to 0 (even) and succeeds.
SUBSTRBYTES_FRAC_NEG_IDX_SUCCESS_TESTS: list[SubstrBytesTest] = [
    SubstrBytesTest(
        "frac_neg_idx_double_minus_0_5",
        string="hello",
        byte_index=-0.5,
        byte_count=5,
        expected="hello",
        msg="$substrBytes should truncate -0.5 start to 0",
    ),
    SubstrBytesTest(
        "frac_neg_idx_double_minus_0_9",
        string="hello",
        byte_index=-0.9,
        byte_count=5,
        expected="hello",
        msg="$substrBytes should truncate -0.9 start to 0",
    ),
    SubstrBytesTest(
        "frac_neg_idx_decimal_minus_0_5",
        string="hello",
        byte_index=DECIMAL128_NEGATIVE_HALF,
        byte_count=5,
        expected="hello",
        msg="$substrBytes should round Decimal128 -0.5 start to 0 (even)",
    ),
]

# Property [Fractional Negative Boundary for Count - Success]: fractional doubles between -1
# exclusive and 0 exclusive truncate to 0 and produce an empty string, and Decimal128 "-0.5" rounds
# to 0 (even) and produces an empty string.
SUBSTRBYTES_FRAC_NEG_CNT_SUCCESS_TESTS: list[SubstrBytesTest] = [
    SubstrBytesTest(
        "frac_neg_cnt_double_minus_0_5",
        string="hello",
        byte_index=0,
        byte_count=-0.5,
        expected="",
        msg="$substrBytes should truncate -0.5 length to 0",
    ),
    SubstrBytesTest(
        "frac_neg_cnt_double_minus_0_9",
        string="hello",
        byte_index=0,
        byte_count=-0.9,
        expected="",
        msg="$substrBytes should truncate -0.9 length to 0",
    ),
    SubstrBytesTest(
        "frac_neg_cnt_decimal_minus_0_5",
        string="hello",
        byte_index=0,
        byte_count=DECIMAL128_NEGATIVE_HALF,
        expected="",
        msg="$substrBytes should round Decimal128 -0.5 length to 0 (even)",
    ),
]

# Property [Fractional Negative Boundary for Count - Negative]: fractional values that round or
# truncate to -1 or below behave as negative byte_count and return the rest of the string.
SUBSTRBYTES_FRAC_NEG_CNT_NEG_TESTS: list[SubstrBytesTest] = [
    SubstrBytesTest(
        "frac_neg_cnt_double_minus_1_0",
        string="hello",
        byte_index=0,
        byte_count=-1.0,
        expected="hello",
        msg="$substrBytes should treat -1.0 length as negative and return rest of string",
    ),
    SubstrBytesTest(
        "frac_neg_cnt_decimal_minus_1_5",
        string="hello",
        byte_index=0,
        byte_count=DECIMAL128_NEGATIVE_ONE_AND_HALF,
        expected="hello",
        msg="$substrBytes should round Decimal128 -1.5 length to -2 and return rest of string",
    ),
]

# Property [Decimal128 Special Values in byte_count]: Decimal128 NaN, Infinity, -Infinity, and
# values that overflow int64 range coerce to int64 min for byte_count, which is negative, so they
# return the rest of the string from the start position.
SUBSTRBYTES_DECIMAL128_SPECIAL_COUNT_TESTS: list[SubstrBytesTest] = [
    SubstrBytesTest(
        "dec_special_cnt_nan",
        string="hello",
        byte_index=0,
        byte_count=Decimal128("NaN"),
        expected="hello",
        msg="$substrBytes should treat Decimal128 NaN length as negative",
    ),
    SubstrBytesTest(
        "dec_special_cnt_inf",
        string="hello",
        byte_index=0,
        byte_count=DECIMAL128_INFINITY,
        expected="hello",
        msg="$substrBytes should treat Decimal128 Infinity length as negative",
    ),
    SubstrBytesTest(
        "dec_special_cnt_neg_inf",
        string="hello",
        byte_index=0,
        byte_count=DECIMAL128_NEGATIVE_INFINITY,
        expected="hello",
        msg="$substrBytes should treat Decimal128 -Infinity length as negative",
    ),
    SubstrBytesTest(
        "dec_special_cnt_nan_from_middle",
        string="hello",
        byte_index=2,
        byte_count=Decimal128("NaN"),
        expected="llo",
        msg="$substrBytes should return rest from middle with Decimal128 NaN length",
    ),
    SubstrBytesTest(
        "dec_special_cnt_overflow_1e6144",
        string="hello",
        byte_index=0,
        byte_count=DECIMAL128_LARGE_EXPONENT,
        expected="hello",
        msg="$substrBytes should treat Decimal128 1E+6144 length as negative overflow",
    ),
    SubstrBytesTest(
        "dec_special_cnt_overflow_max",
        string="hello",
        byte_index=0,
        byte_count=Decimal128("9999999999999999999999999999999999E+6111"),
        expected="hello",
        msg="$substrBytes should treat Decimal128 max value length as negative overflow",
    ),
    SubstrBytesTest(
        "dec_special_cnt_overflow_34_digit",
        string="hello",
        byte_index=0,
        byte_count=Decimal128("9999999999999999999999999999999999"),
        expected="hello",
        msg="$substrBytes should treat Decimal128 34-digit length as negative overflow",
    ),
]


SUBSTRBYTES_NUMERIC_COERCION_ALL_TESTS = (
    SUBSTRBYTES_NUMERIC_COERCION_TESTS
    + SUBSTRBYTES_FRAC_NEG_IDX_SUCCESS_TESTS
    + SUBSTRBYTES_FRAC_NEG_CNT_SUCCESS_TESTS
    + SUBSTRBYTES_FRAC_NEG_CNT_NEG_TESTS
    + SUBSTRBYTES_DECIMAL128_SPECIAL_COUNT_TESTS
)


@pytest.mark.parametrize("op", OPERATORS)
@pytest.mark.parametrize("test_case", pytest_params(SUBSTRBYTES_NUMERIC_COERCION_ALL_TESTS))
def test_substrbytes_numeric_coercion(collection, op, test_case: SubstrBytesTest):
    """Test $substrBytes cases."""
    result = execute_expression(collection, _expr(test_case, op))
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
