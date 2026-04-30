from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import (
    INDEXOF_INDEX_TYPE_ERROR,
    INDEXOF_NEGATIVE_INDEX_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_OVERFLOW,
    INT32_UNDERFLOW,
    INT64_ZERO,
)

from .utils.indexOfCP_common import (
    IndexOfCPTest,
)

# Property [Index Type Acceptance]: integral Decimal128, Int64, and whole-number floats are accepted
# for start and end.
INDEXOFCP_INDEX_TYPE_TESTS: list[IndexOfCPTest] = [
    IndexOfCPTest(
        "idx_type_float_start",
        args=["hello", "lo", 3.0],
        expected=3,
        msg="$indexOfCP should accept whole-number float as start",
    ),
    IndexOfCPTest(
        "idx_type_float_start_and_end",
        args=["hello", "lo", DOUBLE_ZERO, 5.0],
        expected=3,
        msg="$indexOfCP should accept whole-number floats as start and end",
    ),
    IndexOfCPTest(
        "idx_type_decimal128_start",
        args=["hello", "lo", Decimal128("3")],
        expected=3,
        msg="$indexOfCP should accept Decimal128 as start",
    ),
    IndexOfCPTest(
        "idx_type_decimal128_start_and_end",
        args=["hello", "lo", DECIMAL128_ZERO, Decimal128("5")],
        expected=3,
        msg="$indexOfCP should accept Decimal128 as start and end",
    ),
    IndexOfCPTest(
        "idx_type_int64_start",
        args=["hello", "lo", Int64(3)],
        expected=3,
        msg="$indexOfCP should accept Int64 as start",
    ),
    IndexOfCPTest(
        "idx_type_int64_start_and_end",
        args=["hello", "lo", INT64_ZERO, Int64(5)],
        expected=3,
        msg="$indexOfCP should accept Int64 as start and end",
    ),
]


# Property [Numeric Edge Cases - Success]: negative zero, Decimal128 with trailing zeros, and
# Decimal128 exponent notation are accepted as start and end values.
INDEXOFCP_NUMERIC_EDGE_SUCCESS_TESTS: list[IndexOfCPTest] = [
    IndexOfCPTest(
        "num_edge_neg_zero_float_start",
        args=["hello", "h", DOUBLE_NEGATIVE_ZERO],
        expected=0,
        msg="$indexOfCP should treat -0.0 float start as 0",
    ),
    IndexOfCPTest(
        "num_edge_neg_zero_decimal_start",
        args=["hello", "h", DECIMAL128_NEGATIVE_ZERO],
        expected=0,
        msg="$indexOfCP should treat Decimal128 negative zero start as 0",
    ),
    # end=0 means the search range is empty, so no match.
    IndexOfCPTest(
        "num_edge_neg_zero_float_end",
        args=["hello", "h", 0, DOUBLE_NEGATIVE_ZERO],
        expected=-1,
        msg="$indexOfCP should treat -0.0 float end as 0 yielding empty range",
    ),
    IndexOfCPTest(
        "num_edge_neg_zero_decimal_end",
        args=["hello", "h", 0, DECIMAL128_NEGATIVE_ZERO],
        expected=-1,
        msg="$indexOfCP should treat Decimal128 negative zero end as 0 yielding empty range",
    ),
    IndexOfCPTest(
        "num_edge_decimal_trailing_zeros_start",
        args=["hello", "lo", Decimal128("3.0")],
        expected=3,
        msg="$indexOfCP should accept Decimal128 with trailing zeros as start",
    ),
    IndexOfCPTest(
        "num_edge_decimal_trailing_zeros_end",
        args=["hello", "lo", 0, Decimal128("5.0")],
        expected=3,
        msg="$indexOfCP should accept Decimal128 with trailing zeros as end",
    ),
    IndexOfCPTest(
        "num_edge_decimal_exponent_start",
        args=["hello", "lo", Decimal128("3E0")],
        expected=3,
        msg="$indexOfCP should accept Decimal128 with exponent notation as start",
    ),
    IndexOfCPTest(
        "num_edge_decimal_exponent_end",
        args=["hello", "lo", 0, Decimal128("5E0")],
        expected=3,
        msg="$indexOfCP should accept Decimal128 with exponent notation as end",
    ),
]

INDEXOFCP_INDEX_TYPE_AND_NUMERIC_EDGE_TESTS = (
    INDEXOFCP_INDEX_TYPE_TESTS + INDEXOFCP_NUMERIC_EDGE_SUCCESS_TESTS
)


# Property [Negative Index]: negative start or end values produce an error.
INDEXOFCP_NEGATIVE_INDEX_TESTS: list[IndexOfCPTest] = [
    IndexOfCPTest(
        "neg_start",
        args=["hello", "h", -1],
        error_code=INDEXOF_NEGATIVE_INDEX_ERROR,
        msg="$indexOfCP should reject negative int start",
    ),
    IndexOfCPTest(
        "neg_end",
        args=["hello", "h", 0, -1],
        error_code=INDEXOF_NEGATIVE_INDEX_ERROR,
        msg="$indexOfCP should reject negative int end",
    ),
    IndexOfCPTest(
        "neg_both",
        args=["hello", "h", -1, -2],
        error_code=INDEXOF_NEGATIVE_INDEX_ERROR,
        msg="$indexOfCP should reject negative start and end",
    ),
    # Negative floats like -1.0 also produce an error.
    IndexOfCPTest(
        "neg_float_start",
        args=["hello", "h", -1.0],
        error_code=INDEXOF_NEGATIVE_INDEX_ERROR,
        msg="$indexOfCP should reject negative float start",
    ),
    IndexOfCPTest(
        "neg_float_end",
        args=["hello", "h", 0, -1.0],
        error_code=INDEXOF_NEGATIVE_INDEX_ERROR,
        msg="$indexOfCP should reject negative float end",
    ),
    IndexOfCPTest(
        "neg_int64_start",
        args=["hello", "h", Int64(-1)],
        error_code=INDEXOF_NEGATIVE_INDEX_ERROR,
        msg="$indexOfCP should reject negative Int64 start",
    ),
    IndexOfCPTest(
        "neg_int64_end",
        args=["hello", "h", 0, Int64(-1)],
        error_code=INDEXOF_NEGATIVE_INDEX_ERROR,
        msg="$indexOfCP should reject negative Int64 end",
    ),
    IndexOfCPTest(
        "neg_decimal_start",
        args=["hello", "h", Decimal128("-1")],
        error_code=INDEXOF_NEGATIVE_INDEX_ERROR,
        msg="$indexOfCP should reject negative Decimal128 start",
    ),
    IndexOfCPTest(
        "neg_decimal_end",
        args=["hello", "h", 0, Decimal128("-1")],
        error_code=INDEXOF_NEGATIVE_INDEX_ERROR,
        msg="$indexOfCP should reject negative Decimal128 end",
    ),
]


# Property [Numeric Edge Cases - Error]: NaN, infinity, and out-of-int32-range values are rejected
# as start and end arguments.
INDEXOFCP_NUMERIC_EDGE_ERROR_TESTS: list[IndexOfCPTest] = [
    IndexOfCPTest(
        "num_edge_nan_start",
        args=["hello", "h", FLOAT_NAN],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfCP should reject NaN float as start",
    ),
    IndexOfCPTest(
        "num_edge_nan_end",
        args=["hello", "h", 0, FLOAT_NAN],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfCP should reject NaN float as end",
    ),
    IndexOfCPTest(
        "num_edge_decimal_nan_start",
        args=["hello", "h", DECIMAL128_NAN],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfCP should reject Decimal128 NaN as start",
    ),
    IndexOfCPTest(
        "num_edge_decimal_nan_end",
        args=["hello", "h", 0, DECIMAL128_NAN],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfCP should reject Decimal128 NaN as end",
    ),
    IndexOfCPTest(
        "num_edge_inf_start",
        args=["hello", "h", FLOAT_INFINITY],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfCP should reject positive infinity as start",
    ),
    IndexOfCPTest(
        "num_edge_inf_end",
        args=["hello", "h", 0, FLOAT_INFINITY],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfCP should reject positive infinity as end",
    ),
    IndexOfCPTest(
        "num_edge_neg_inf_start",
        args=["hello", "h", FLOAT_NEGATIVE_INFINITY],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfCP should reject negative infinity as start",
    ),
    IndexOfCPTest(
        "num_edge_neg_inf_end",
        args=["hello", "h", 0, FLOAT_NEGATIVE_INFINITY],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfCP should reject negative infinity as end",
    ),
    IndexOfCPTest(
        "num_edge_decimal_inf_start",
        args=["hello", "h", DECIMAL128_INFINITY],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfCP should reject Decimal128 infinity as start",
    ),
    IndexOfCPTest(
        "num_edge_decimal_inf_end",
        args=["hello", "h", 0, DECIMAL128_INFINITY],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfCP should reject Decimal128 infinity as end",
    ),
    IndexOfCPTest(
        "num_edge_decimal_neg_inf_start",
        args=["hello", "h", DECIMAL128_NEGATIVE_INFINITY],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfCP should reject Decimal128 negative infinity as start",
    ),
    IndexOfCPTest(
        "num_edge_decimal_neg_inf_end",
        args=["hello", "h", 0, DECIMAL128_NEGATIVE_INFINITY],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfCP should reject Decimal128 negative infinity as end",
    ),
    IndexOfCPTest(
        "num_edge_int64_over_max_start",
        args=["hello", "h", Int64(INT32_OVERFLOW)],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfCP should reject Int64 above int32 max as start",
    ),
    IndexOfCPTest(
        "num_edge_int64_over_max_end",
        args=["hello", "h", 0, Int64(INT32_OVERFLOW)],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfCP should reject Int64 above int32 max as end",
    ),
    IndexOfCPTest(
        "num_edge_decimal_over_max_start",
        args=["hello", "h", Decimal128("2147483648")],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfCP should reject Decimal128 above int32 max as start",
    ),
    IndexOfCPTest(
        "num_edge_decimal_over_max_end",
        args=["hello", "h", 0, Decimal128("2147483648")],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfCP should reject Decimal128 above int32 max as end",
    ),
    # The int32 range check takes precedence over the negative check.
    IndexOfCPTest(
        "num_edge_int64_under_min_start",
        args=["hello", "h", Int64(INT32_UNDERFLOW)],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfCP int32 range error should precede negative error for start",
    ),
    IndexOfCPTest(
        "num_edge_int64_under_min_end",
        args=["hello", "h", 0, Int64(INT32_UNDERFLOW)],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfCP int32 range error should precede negative error for end",
    ),
]

INDEXOFCP_ALL_INDEX_TESTS = (
    INDEXOFCP_INDEX_TYPE_AND_NUMERIC_EDGE_TESTS
    + INDEXOFCP_NEGATIVE_INDEX_TESTS
    + INDEXOFCP_NUMERIC_EDGE_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(INDEXOFCP_ALL_INDEX_TESTS))
def test_indexofcp_index_types(collection, test_case: IndexOfCPTest):
    """Test $indexOfCP index type acceptance and expression arguments."""
    result = execute_expression(collection, {"$indexOfCP": test_case.args})
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
