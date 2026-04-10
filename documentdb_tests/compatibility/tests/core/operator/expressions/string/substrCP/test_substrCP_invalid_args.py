from __future__ import annotations

import pytest
from bson import Decimal128, Int64

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
    SUBSTRCP_COUNT_NEGATIVE_ERROR,
    SUBSTRCP_COUNT_NON_INT_ERROR,
    SUBSTRCP_COUNT_TYPE_ERROR,
    SUBSTRCP_INDEX_NEGATIVE_ERROR,
    SUBSTRCP_INDEX_NON_INT_ERROR,
    SUBSTRCP_INDEX_TYPE_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_ONE_AND_HALF,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_OVERFLOW,
    INT32_UNDERFLOW,
    INT64_MAX,
    INT64_MIN,
)

from .utils.substrCP_common import SubstrCPTest, _expr

# Property [Arity]: $substrCP requires exactly 3 arguments in an array.
SUBSTRCP_ARITY_TESTS: list[SubstrCPTest] = [
    SubstrCPTest(
        "arity_zero",
        raw_args=[],
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$substrCP should reject 0 arguments",
    ),
    SubstrCPTest(
        "arity_one",
        raw_args=["hello"],
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$substrCP should reject 1 argument",
    ),
    SubstrCPTest(
        "arity_two",
        raw_args=["hello", 0],
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$substrCP should reject 2 arguments",
    ),
    SubstrCPTest(
        "arity_four",
        raw_args=["hello", 0, 1, 2],
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$substrCP should reject 4 arguments",
    ),
    SubstrCPTest(
        "arity_bare_value",
        raw_args="hello",
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$substrCP should reject a bare value instead of an array",
    ),
    SubstrCPTest(
        "arity_bare_null",
        raw_args=None,
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$substrCP should reject bare null argument",
    ),
]


# Property [Field Path Parsing]: invalid field path syntax produces parse-time errors.
SUBSTRCP_FIELD_PATH_TESTS: list[SubstrCPTest] = [
    SubstrCPTest(
        "fieldpath_bare_dollar",
        string="$",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$substrCP should reject bare '$' as invalid field path",
    ),
    SubstrCPTest(
        "fieldpath_double_dollar",
        string="$$",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$substrCP should reject '$$' as empty variable name",
    ),
    SubstrCPTest(
        "fieldpath_null_byte",
        string="$a\x00b",
        error_code=FIELD_PATH_NULL_BYTE_ERROR,
        msg="$substrCP should reject field path containing null byte",
    ),
    SubstrCPTest(
        "fieldpath_bare_dollar_index",
        string="hello",
        index="$",
        count=1,
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$substrCP should reject bare '$' as index",
    ),
    SubstrCPTest(
        "fieldpath_double_dollar_index",
        string="hello",
        index="$$",
        count=1,
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$substrCP should reject '$$' as index",
    ),
    SubstrCPTest(
        "fieldpath_null_byte_index",
        string="hello",
        index="$a\x00b",
        count=1,
        error_code=FIELD_PATH_NULL_BYTE_ERROR,
        msg="$substrCP should reject field path with null byte as index",
    ),
    SubstrCPTest(
        "fieldpath_bare_dollar_count",
        string="hello",
        index=0,
        count="$",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$substrCP should reject bare '$' as count",
    ),
    SubstrCPTest(
        "fieldpath_double_dollar_count",
        string="hello",
        index=0,
        count="$$",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$substrCP should reject '$$' as count",
    ),
    SubstrCPTest(
        "fieldpath_null_byte_count",
        string="hello",
        index=0,
        count="$a\x00b",
        error_code=FIELD_PATH_NULL_BYTE_ERROR,
        msg="$substrCP should reject field path with null byte as count",
    ),
]


# Property [Non-Integer Index]: fractional, NaN, infinity, and out-of-range numeric values for the
# index produce an error.
SUBSTRCP_INDEX_NON_INT_TESTS: list[SubstrCPTest] = [
    SubstrCPTest(
        "nonint_index_frac_double",
        string="hello",
        index=1.5,
        error_code=SUBSTRCP_INDEX_NON_INT_ERROR,
        msg="$substrCP should reject fractional double as index",
    ),
    SubstrCPTest(
        "nonint_index_nan",
        string="hello",
        index=FLOAT_NAN,
        error_code=SUBSTRCP_INDEX_NON_INT_ERROR,
        msg="$substrCP should reject NaN double as index",
    ),
    SubstrCPTest(
        "nonint_index_inf",
        string="hello",
        index=FLOAT_INFINITY,
        error_code=SUBSTRCP_INDEX_NON_INT_ERROR,
        msg="$substrCP should reject positive infinity as index",
    ),
    SubstrCPTest(
        "nonint_index_neg_inf",
        string="hello",
        index=FLOAT_NEGATIVE_INFINITY,
        error_code=SUBSTRCP_INDEX_NON_INT_ERROR,
        msg="$substrCP should reject negative infinity as index",
    ),
    SubstrCPTest(
        "nonint_index_large_double",
        string="hello",
        index=1e20,
        error_code=SUBSTRCP_INDEX_NON_INT_ERROR,
        msg="$substrCP should reject large double outside int32 range as index",
    ),
    SubstrCPTest(
        "nonint_index_int64_overflow",
        string="hello",
        index=Int64(INT32_OVERFLOW),
        error_code=SUBSTRCP_INDEX_NON_INT_ERROR,
        msg="$substrCP should reject Int64 above int32 range as index",
    ),
    SubstrCPTest(
        "nonint_index_int64_max",
        string="hello",
        index=INT64_MAX,
        error_code=SUBSTRCP_INDEX_NON_INT_ERROR,
        msg="$substrCP should reject Int64 max as index",
    ),
    SubstrCPTest(
        "nonint_index_int64_min",
        string="hello",
        index=INT64_MIN,
        error_code=SUBSTRCP_INDEX_NON_INT_ERROR,
        msg="$substrCP should reject Int64 min as index",
    ),
    SubstrCPTest(
        "nonint_index_frac_decimal128",
        string="hello",
        index=DECIMAL128_ONE_AND_HALF,
        error_code=SUBSTRCP_INDEX_NON_INT_ERROR,
        msg="$substrCP should reject fractional Decimal128 as index",
    ),
    SubstrCPTest(
        "nonint_index_decimal128_nan",
        string="hello",
        index=Decimal128("NaN"),
        error_code=SUBSTRCP_INDEX_NON_INT_ERROR,
        msg="$substrCP should reject Decimal128 NaN as index",
    ),
    SubstrCPTest(
        "nonint_index_decimal128_inf",
        string="hello",
        index=DECIMAL128_INFINITY,
        error_code=SUBSTRCP_INDEX_NON_INT_ERROR,
        msg="$substrCP should reject Decimal128 Infinity as index",
    ),
    SubstrCPTest(
        "nonint_index_decimal128_neg_inf",
        string="hello",
        index=DECIMAL128_NEGATIVE_INFINITY,
        error_code=SUBSTRCP_INDEX_NON_INT_ERROR,
        msg="$substrCP should reject Decimal128 negative Infinity as index",
    ),
    SubstrCPTest(
        "nonint_index_decimal128_out_of_range",
        string="hello",
        index=Decimal128("3000000000"),
        error_code=SUBSTRCP_INDEX_NON_INT_ERROR,
        msg="$substrCP should reject out-of-range Decimal128 as index",
    ),
    # 0.9999999999999999 displays as "1" but is not exactly representable as an integer.
    SubstrCPTest(
        "nonint_index_nearly_int",
        string="hello",
        index=0.9999999999999999,
        error_code=SUBSTRCP_INDEX_NON_INT_ERROR,
        msg="$substrCP should reject double that displays as integer but is not exact",
    ),
]


# Property [Non-Integer Count]: fractional, NaN, infinity, and out-of-range numeric values for the
# count produce an error.
SUBSTRCP_COUNT_NON_INT_TESTS: list[SubstrCPTest] = [
    SubstrCPTest(
        "nonint_count_frac_double",
        string="hello",
        index=0,
        count=1.5,
        error_code=SUBSTRCP_COUNT_NON_INT_ERROR,
        msg="$substrCP should reject fractional double as count",
    ),
    SubstrCPTest(
        "nonint_count_nan",
        string="hello",
        index=0,
        count=FLOAT_NAN,
        error_code=SUBSTRCP_COUNT_NON_INT_ERROR,
        msg="$substrCP should reject NaN double as count",
    ),
    SubstrCPTest(
        "nonint_count_inf",
        string="hello",
        index=0,
        count=FLOAT_INFINITY,
        error_code=SUBSTRCP_COUNT_NON_INT_ERROR,
        msg="$substrCP should reject positive infinity as count",
    ),
    SubstrCPTest(
        "nonint_count_neg_inf",
        string="hello",
        index=0,
        count=FLOAT_NEGATIVE_INFINITY,
        error_code=SUBSTRCP_COUNT_NON_INT_ERROR,
        msg="$substrCP should reject negative infinity as count",
    ),
    SubstrCPTest(
        "nonint_count_large_double",
        string="hello",
        index=0,
        count=1e20,
        error_code=SUBSTRCP_COUNT_NON_INT_ERROR,
        msg="$substrCP should reject large double outside int32 range as count",
    ),
    SubstrCPTest(
        "nonint_count_int64_overflow",
        string="hello",
        index=0,
        count=Int64(INT32_OVERFLOW),
        error_code=SUBSTRCP_COUNT_NON_INT_ERROR,
        msg="$substrCP should reject Int64 above int32 range as count",
    ),
    SubstrCPTest(
        "nonint_count_int64_max",
        string="hello",
        index=0,
        count=INT64_MAX,
        error_code=SUBSTRCP_COUNT_NON_INT_ERROR,
        msg="$substrCP should reject Int64 max as count",
    ),
    SubstrCPTest(
        "nonint_count_int64_min",
        string="hello",
        index=0,
        count=INT64_MIN,
        error_code=SUBSTRCP_COUNT_NON_INT_ERROR,
        msg="$substrCP should reject Int64 min as count",
    ),
    SubstrCPTest(
        "nonint_count_frac_decimal128",
        string="hello",
        index=0,
        count=DECIMAL128_ONE_AND_HALF,
        error_code=SUBSTRCP_COUNT_NON_INT_ERROR,
        msg="$substrCP should reject fractional Decimal128 as count",
    ),
    SubstrCPTest(
        "nonint_count_decimal128_nan",
        string="hello",
        index=0,
        count=Decimal128("NaN"),
        error_code=SUBSTRCP_COUNT_NON_INT_ERROR,
        msg="$substrCP should reject Decimal128 NaN as count",
    ),
    SubstrCPTest(
        "nonint_count_decimal128_inf",
        string="hello",
        index=0,
        count=DECIMAL128_INFINITY,
        error_code=SUBSTRCP_COUNT_NON_INT_ERROR,
        msg="$substrCP should reject Decimal128 Infinity as count",
    ),
    SubstrCPTest(
        "nonint_count_decimal128_neg_inf",
        string="hello",
        index=0,
        count=DECIMAL128_NEGATIVE_INFINITY,
        error_code=SUBSTRCP_COUNT_NON_INT_ERROR,
        msg="$substrCP should reject Decimal128 negative Infinity as count",
    ),
    SubstrCPTest(
        "nonint_count_decimal128_out_of_range",
        string="hello",
        index=0,
        count=Decimal128("3000000000"),
        error_code=SUBSTRCP_COUNT_NON_INT_ERROR,
        msg="$substrCP should reject out-of-range Decimal128 as count",
    ),
    # 3.0000000000000004 displays as "3" but is not exactly representable as an integer.
    SubstrCPTest(
        "nonint_count_nearly_int",
        string="hello",
        index=0,
        count=3.0000000000000004,
        error_code=SUBSTRCP_COUNT_NON_INT_ERROR,
        msg="$substrCP should reject double that displays as integer but is not exact",
    ),
    SubstrCPTest(
        "nonint_count_expr_imprecision",
        string="hello",
        index=0,
        count={"$add": [0.1, 0.2]},
        error_code=SUBSTRCP_COUNT_NON_INT_ERROR,
        msg="$substrCP should reject expression result with floating-point imprecision",
    ),
]


# Property [Negative Index]: negative int32 and Int64 values within int32 range produce an error.
SUBSTRCP_INDEX_NEGATIVE_TESTS: list[SubstrCPTest] = [
    SubstrCPTest(
        "neg_index_int32",
        string="hello",
        index=-1,
        error_code=SUBSTRCP_INDEX_NEGATIVE_ERROR,
        msg="$substrCP should reject negative int32 index",
    ),
    SubstrCPTest(
        "neg_index_int64",
        string="hello",
        index=Int64(-1),
        error_code=SUBSTRCP_INDEX_NEGATIVE_ERROR,
        msg="$substrCP should reject negative Int64 index within int32 range",
    ),
    # Out-of-range negative fires the non-int check before the negative check.
    SubstrCPTest(
        "neg_index_out_of_range",
        string="hello",
        index=Int64(INT32_UNDERFLOW),
        error_code=SUBSTRCP_INDEX_NON_INT_ERROR,
        msg="$substrCP should reject out-of-range negative index with non-int error",
    ),
]


# Property [Negative Count]: negative int32 and Int64 values within int32 range produce an error.
SUBSTRCP_COUNT_NEGATIVE_TESTS: list[SubstrCPTest] = [
    SubstrCPTest(
        "neg_count_int32",
        string="hello",
        index=0,
        count=-1,
        error_code=SUBSTRCP_COUNT_NEGATIVE_ERROR,
        msg="$substrCP should reject negative int32 count",
    ),
    SubstrCPTest(
        "neg_count_int64",
        string="hello",
        index=0,
        count=Int64(-1),
        error_code=SUBSTRCP_COUNT_NEGATIVE_ERROR,
        msg="$substrCP should reject negative Int64 count within int32 range",
    ),
    # Out-of-range negative fires the non-int check before the negative check.
    SubstrCPTest(
        "neg_count_out_of_range",
        string="hello",
        index=0,
        count=Int64(INT32_UNDERFLOW),
        error_code=SUBSTRCP_COUNT_NON_INT_ERROR,
        msg="$substrCP should reject out-of-range negative count with non-int error",
    ),
]


# Property [Error Precedence]: errors are evaluated in priority order: string type before index
# type before index non-integer before count type before count non-integer before count negative
# before index negative.
SUBSTRCP_ERROR_PRECEDENCE_TESTS: list[SubstrCPTest] = [
    SubstrCPTest(
        "prec_string_over_index_type",
        string=True,
        index="bad",
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$substrCP string type error should take precedence over index type error",
    ),
    SubstrCPTest(
        "prec_string_over_count_type",
        string=True,
        index=0,
        count="bad",
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$substrCP string type error should take precedence over count type error",
    ),
    SubstrCPTest(
        "prec_index_type_over_count_nonint",
        string="hello",
        index="bad",
        count=1.5,
        error_code=SUBSTRCP_INDEX_TYPE_ERROR,
        msg="$substrCP index type error should take precedence over count non-integer",
    ),
    SubstrCPTest(
        "prec_index_nonint_over_count_type",
        string="hello",
        index=1.5,
        count="bad",
        error_code=SUBSTRCP_INDEX_NON_INT_ERROR,
        msg="$substrCP index non-integer should take precedence over count type error",
    ),
    SubstrCPTest(
        "prec_index_nonint_over_count_nonint",
        string="hello",
        index=1.5,
        count=1.5,
        error_code=SUBSTRCP_INDEX_NON_INT_ERROR,
        msg="$substrCP index non-integer should take precedence over count non-integer",
    ),
    SubstrCPTest(
        "prec_count_type_over_index_neg",
        string="hello",
        index=-1,
        count="bad",
        error_code=SUBSTRCP_COUNT_TYPE_ERROR,
        msg="$substrCP count type error should take precedence over index negative",
    ),
    SubstrCPTest(
        "prec_count_nonint_over_index_neg",
        string="hello",
        index=-1,
        count=1.5,
        error_code=SUBSTRCP_COUNT_NON_INT_ERROR,
        msg="$substrCP count non-integer should take precedence over index negative",
    ),
    SubstrCPTest(
        "prec_count_neg_over_index_neg",
        string="hello",
        index=-1,
        count=-1,
        error_code=SUBSTRCP_COUNT_NEGATIVE_ERROR,
        msg="$substrCP count negative should take precedence over index negative",
    ),
]


SUBSTRCP_INVALID_ARGS_ALL_TESTS = (
    SUBSTRCP_ARITY_TESTS
    + SUBSTRCP_FIELD_PATH_TESTS
    + SUBSTRCP_INDEX_NON_INT_TESTS
    + SUBSTRCP_COUNT_NON_INT_TESTS
    + SUBSTRCP_INDEX_NEGATIVE_TESTS
    + SUBSTRCP_COUNT_NEGATIVE_TESTS
    + SUBSTRCP_ERROR_PRECEDENCE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SUBSTRCP_INVALID_ARGS_ALL_TESTS))
def test_substrcp_invalid_args(collection, test_case: SubstrCPTest):
    """Test $substrCP invalid argument cases."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
