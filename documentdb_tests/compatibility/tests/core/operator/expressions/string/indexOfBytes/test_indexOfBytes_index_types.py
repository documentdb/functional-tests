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

from .utils.indexOfBytes_common import (
    IndexOfBytesTest,
)

# Property [Index Type Acceptance]: integral Decimal128, Int64, and whole-number floats are accepted
# for start and end.
INDEXOFBYTES_INDEX_TYPE_TESTS: list[IndexOfBytesTest] = [
    IndexOfBytesTest(
        "idx_type_float_start",
        args=["hello", "lo", 3.0],
        expected=3,
        msg="$indexOfBytes should accept whole-number float as start",
    ),
    IndexOfBytesTest(
        "idx_type_float_start_and_end",
        args=["hello", "lo", DOUBLE_ZERO, 5.0],
        expected=3,
        msg="$indexOfBytes should accept whole-number floats as start and end",
    ),
    IndexOfBytesTest(
        "idx_type_decimal128_start",
        args=["hello", "lo", Decimal128("3")],
        expected=3,
        msg="$indexOfBytes should accept Decimal128 as start",
    ),
    IndexOfBytesTest(
        "idx_type_decimal128_start_and_end",
        args=["hello", "lo", DECIMAL128_ZERO, Decimal128("5")],
        expected=3,
        msg="$indexOfBytes should accept Decimal128 as start and end",
    ),
    IndexOfBytesTest(
        "idx_type_int64_start",
        args=["hello", "lo", Int64(3)],
        expected=3,
        msg="$indexOfBytes should accept Int64 as start",
    ),
    IndexOfBytesTest(
        "idx_type_int64_start_and_end",
        args=["hello", "lo", INT64_ZERO, Int64(5)],
        expected=3,
        msg="$indexOfBytes should accept Int64 as start and end",
    ),
]

# Property [Numeric Edge Cases]: negative zero is treated as 0, and Decimal128 with trailing zeros
# or exponent notation resolving to an integer is accepted.
INDEXOFBYTES_NUMERIC_EDGE_SUCCESS_TESTS: list[IndexOfBytesTest] = [
    IndexOfBytesTest(
        "num_edge_neg_zero_float_start",
        args=["hello", "h", DOUBLE_NEGATIVE_ZERO],
        expected=0,
        msg="$indexOfBytes should treat -0.0 float start as 0",
    ),
    IndexOfBytesTest(
        "num_edge_neg_zero_decimal_start",
        args=["hello", "h", DECIMAL128_NEGATIVE_ZERO],
        expected=0,
        msg="$indexOfBytes should treat Decimal128 negative zero start as 0",
    ),
    # end=0 means the search range is empty, so no match.
    IndexOfBytesTest(
        "num_edge_neg_zero_float_end",
        args=["hello", "h", 0, DOUBLE_NEGATIVE_ZERO],
        expected=-1,
        msg="$indexOfBytes should treat -0.0 float end as 0 yielding empty range",
    ),
    IndexOfBytesTest(
        "num_edge_neg_zero_decimal_end",
        args=["hello", "h", 0, DECIMAL128_NEGATIVE_ZERO],
        expected=-1,
        msg="$indexOfBytes should treat Decimal128 negative zero end as 0 yielding empty range",
    ),
    IndexOfBytesTest(
        "num_edge_decimal_trailing_zeros_start",
        args=["hello", "lo", Decimal128("3.0")],
        expected=3,
        msg="$indexOfBytes should accept Decimal128 with trailing zeros as start",
    ),
    IndexOfBytesTest(
        "num_edge_decimal_trailing_zeros_end",
        args=["hello", "lo", 0, Decimal128("5.0")],
        expected=3,
        msg="$indexOfBytes should accept Decimal128 with trailing zeros as end",
    ),
    IndexOfBytesTest(
        "num_edge_decimal_exponent_start",
        args=["hello", "lo", Decimal128("3E0")],
        expected=3,
        msg="$indexOfBytes should accept Decimal128 with exponent notation as start",
    ),
    IndexOfBytesTest(
        "num_edge_decimal_exponent_end",
        args=["hello", "lo", 0, Decimal128("5E0")],
        expected=3,
        msg="$indexOfBytes should accept Decimal128 with exponent notation as end",
    ),
]

# Property [Negative Index]: negative start or end values produce an error.
INDEXOFBYTES_NEGATIVE_INDEX_TESTS: list[IndexOfBytesTest] = [
    IndexOfBytesTest(
        "neg_start",
        args=["hello", "h", -1],
        error_code=INDEXOF_NEGATIVE_INDEX_ERROR,
        msg="$indexOfBytes should reject negative int start",
    ),
    IndexOfBytesTest(
        "neg_end",
        args=["hello", "h", 0, -1],
        error_code=INDEXOF_NEGATIVE_INDEX_ERROR,
        msg="$indexOfBytes should reject negative int end",
    ),
    IndexOfBytesTest(
        "neg_both",
        args=["hello", "h", -1, -2],
        error_code=INDEXOF_NEGATIVE_INDEX_ERROR,
        msg="$indexOfBytes should reject negative start and end",
    ),
    # Negative floats like -1.0 also produce an error.
    IndexOfBytesTest(
        "neg_float_start",
        args=["hello", "h", -1.0],
        error_code=INDEXOF_NEGATIVE_INDEX_ERROR,
        msg="$indexOfBytes should reject negative float start",
    ),
    IndexOfBytesTest(
        "neg_float_end",
        args=["hello", "h", 0, -1.0],
        error_code=INDEXOF_NEGATIVE_INDEX_ERROR,
        msg="$indexOfBytes should reject negative float end",
    ),
    IndexOfBytesTest(
        "neg_int64_start",
        args=["hello", "h", Int64(-1)],
        error_code=INDEXOF_NEGATIVE_INDEX_ERROR,
        msg="$indexOfBytes should reject negative Int64 start",
    ),
    IndexOfBytesTest(
        "neg_int64_end",
        args=["hello", "h", 0, Int64(-1)],
        error_code=INDEXOF_NEGATIVE_INDEX_ERROR,
        msg="$indexOfBytes should reject negative Int64 end",
    ),
    IndexOfBytesTest(
        "neg_decimal_start",
        args=["hello", "h", Decimal128("-1")],
        error_code=INDEXOF_NEGATIVE_INDEX_ERROR,
        msg="$indexOfBytes should reject negative Decimal128 start",
    ),
    IndexOfBytesTest(
        "neg_decimal_end",
        args=["hello", "h", 0, Decimal128("-1")],
        error_code=INDEXOF_NEGATIVE_INDEX_ERROR,
        msg="$indexOfBytes should reject negative Decimal128 end",
    ),
]

# Property [Numeric Edge Cases - Non-Integral and Out-of-Range Errors]: NaN, infinity, and values
# outside the int32 range produce an index type error for start and end, even when the value is
# negative.
INDEXOFBYTES_NUMERIC_EDGE_ERROR_TESTS: list[IndexOfBytesTest] = [
    IndexOfBytesTest(
        "num_edge_nan_start",
        args=["hello", "h", FLOAT_NAN],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject NaN float as start",
    ),
    IndexOfBytesTest(
        "num_edge_nan_end",
        args=["hello", "h", 0, FLOAT_NAN],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject NaN float as end",
    ),
    IndexOfBytesTest(
        "num_edge_decimal_nan_start",
        args=["hello", "h", Decimal128("NaN")],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject Decimal128 NaN as start",
    ),
    IndexOfBytesTest(
        "num_edge_decimal_nan_end",
        args=["hello", "h", 0, Decimal128("NaN")],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject Decimal128 NaN as end",
    ),
    IndexOfBytesTest(
        "num_edge_inf_start",
        args=["hello", "h", FLOAT_INFINITY],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject positive infinity as start",
    ),
    IndexOfBytesTest(
        "num_edge_inf_end",
        args=["hello", "h", 0, FLOAT_INFINITY],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject positive infinity as end",
    ),
    IndexOfBytesTest(
        "num_edge_neg_inf_start",
        args=["hello", "h", FLOAT_NEGATIVE_INFINITY],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject negative infinity as start",
    ),
    IndexOfBytesTest(
        "num_edge_neg_inf_end",
        args=["hello", "h", 0, FLOAT_NEGATIVE_INFINITY],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject negative infinity as end",
    ),
    IndexOfBytesTest(
        "num_edge_decimal_inf_start",
        args=["hello", "h", DECIMAL128_INFINITY],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject Decimal128 infinity as start",
    ),
    IndexOfBytesTest(
        "num_edge_decimal_inf_end",
        args=["hello", "h", 0, DECIMAL128_INFINITY],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject Decimal128 infinity as end",
    ),
    IndexOfBytesTest(
        "num_edge_decimal_neg_inf_start",
        args=["hello", "h", DECIMAL128_NEGATIVE_INFINITY],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject Decimal128 negative infinity as start",
    ),
    IndexOfBytesTest(
        "num_edge_decimal_neg_inf_end",
        args=["hello", "h", 0, DECIMAL128_NEGATIVE_INFINITY],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject Decimal128 negative infinity as end",
    ),
    IndexOfBytesTest(
        "num_edge_int64_over_max_start",
        args=["hello", "h", Int64(INT32_OVERFLOW)],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject Int64 above int32 max as start",
    ),
    IndexOfBytesTest(
        "num_edge_int64_over_max_end",
        args=["hello", "h", 0, Int64(INT32_OVERFLOW)],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject Int64 above int32 max as end",
    ),
    IndexOfBytesTest(
        "num_edge_decimal_over_max_start",
        args=["hello", "h", Decimal128("2147483648")],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject Decimal128 above int32 max as start",
    ),
    IndexOfBytesTest(
        "num_edge_decimal_over_max_end",
        args=["hello", "h", 0, Decimal128("2147483648")],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject Decimal128 above int32 max as end",
    ),
    # The int32 range check takes precedence over the negative index check.
    IndexOfBytesTest(
        "num_edge_int64_under_min_start",
        args=["hello", "h", Int64(INT32_UNDERFLOW)],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes int32 range error should precede negative error for start",
    ),
    IndexOfBytesTest(
        "num_edge_int64_under_min_end",
        args=["hello", "h", 0, Int64(INT32_UNDERFLOW)],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes int32 range error should precede negative error for end",
    ),
]


INDEXOFBYTES_INDEX_TYPE_ALL_TESTS = (
    INDEXOFBYTES_INDEX_TYPE_TESTS
    + INDEXOFBYTES_NUMERIC_EDGE_SUCCESS_TESTS
    + INDEXOFBYTES_NEGATIVE_INDEX_TESTS
    + INDEXOFBYTES_NUMERIC_EDGE_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(INDEXOFBYTES_INDEX_TYPE_ALL_TESTS))
def test_indexofbytes_cases(collection, test_case: IndexOfBytesTest):
    """Test $indexOfBytes cases."""
    result = execute_expression(collection, {"$indexOfBytes": test_case.args})
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
