"""Tests for $skip stage numeric value errors: negative, fractional, non-finite, overflow."""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import SKIP_INVALID_ARGUMENT_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_INT64_OVERFLOW,
    DECIMAL128_INT64_UNDERFLOW,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MAX_COEFFICIENT,
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_NEGATIVE_ONE_AND_HALF,
    DECIMAL128_SMALL_EXPONENT,
    DOUBLE_FROM_INT64_MAX,
    DOUBLE_MAX,
    DOUBLE_MIN_NORMAL,
    DOUBLE_MIN_SUBNORMAL,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
    INT32_MIN,
    INT64_MIN,
)

# Property [Negative Value Rejection]: $skip rejects negative numeric values
# of all types with an error.
SKIP_NEGATIVE_VALUE_REJECTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "negative_int32",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": -1}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject negative int32 values",
    ),
    StageTestCase(
        "negative_int64",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": Int64(-1)}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject negative int64 values",
    ),
    StageTestCase(
        "negative_double",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": -1.0}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject negative whole-number double values",
    ),
    StageTestCase(
        "negative_decimal128",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": Decimal128("-1")}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject negative Decimal128 values",
    ),
    StageTestCase(
        "int32_min",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": INT32_MIN}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject INT32_MIN",
    ),
    StageTestCase(
        "int64_min",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": INT64_MIN}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject INT64_MIN",
    ),
]

# Property [Fractional Value Rejection]: $skip rejects any numeric value that
# is not exactly representable as a whole number.
SKIP_FRACTIONAL_VALUE_REJECTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "fractional_double",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": 3.5}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject fractional double values",
    ),
    StageTestCase(
        "near_integer_double_above",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": 3.0000000000000004}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject near-integer double just above whole number",
    ),
    StageTestCase(
        "near_integer_double_below",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": 2.9999999999999996}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject near-integer double just below whole number",
    ),
    StageTestCase(
        "subnormal_double",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": DOUBLE_MIN_SUBNORMAL}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject subnormal double values",
    ),
    StageTestCase(
        "dbl_min_normal",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": DOUBLE_MIN_NORMAL}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject DBL_MIN (smallest positive normal double)",
    ),
    StageTestCase(
        "fractional_decimal128",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": Decimal128("3.5")}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject fractional Decimal128 values",
    ),
    StageTestCase(
        "fractional_decimal128_exponent",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": Decimal128("5001E-3")}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject Decimal128 with fractional exponent notation",
    ),
    StageTestCase(
        "decimal128_precision_beyond_integer",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": Decimal128("1.000000000000000000000000000000001")}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject Decimal128 with precision beyond integer",
    ),
    StageTestCase(
        "negative_fractional_double",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": -1.5}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject negative fractional double",
    ),
    StageTestCase(
        "negative_fractional_decimal128",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": DECIMAL128_NEGATIVE_ONE_AND_HALF}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject negative fractional Decimal128",
    ),
    StageTestCase(
        "decimal128_min_positive",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": DECIMAL128_MIN_POSITIVE}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject Decimal128 minimum positive representable",
    ),
    StageTestCase(
        "decimal128_small_exponent",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": DECIMAL128_SMALL_EXPONENT}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject Decimal128 with extreme negative exponent",
    ),
]

# Property [Non-Finite Value Rejection]: $skip rejects NaN and Infinity
# values for both double and Decimal128 types.
SKIP_NON_FINITE_VALUE_REJECTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "double_nan",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": FLOAT_NAN}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject double NaN",
    ),
    StageTestCase(
        "double_negative_nan",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": FLOAT_NEGATIVE_NAN}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject double negative NaN",
    ),
    StageTestCase(
        "decimal128_nan",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": DECIMAL128_NAN}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject Decimal128 NaN",
    ),
    StageTestCase(
        "decimal128_negative_nan",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": DECIMAL128_NEGATIVE_NAN}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject Decimal128 negative NaN",
    ),
    StageTestCase(
        "double_infinity",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": FLOAT_INFINITY}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject double Infinity",
    ),
    StageTestCase(
        "double_negative_infinity",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": FLOAT_NEGATIVE_INFINITY}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject double -Infinity",
    ),
    StageTestCase(
        "decimal128_infinity",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": DECIMAL128_INFINITY}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject Decimal128 Infinity",
    ),
    StageTestCase(
        "decimal128_negative_infinity",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": DECIMAL128_NEGATIVE_INFINITY}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject Decimal128 -Infinity",
    ),
]

# Property [Overflow Rejection]: $skip rejects numeric values that fall
# outside the representable range of a 64-bit signed integer.
SKIP_OVERFLOW_REJECTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "double_above_int64_max",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": DOUBLE_FROM_INT64_MAX}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject double that rounds above INT64_MAX",
    ),
    StageTestCase(
        "double_max",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": DOUBLE_MAX}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject DBL_MAX",
    ),
    StageTestCase(
        "decimal128_above_int64_max",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": DECIMAL128_INT64_OVERFLOW}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject Decimal128 exceeding INT64_MAX",
    ),
    StageTestCase(
        "decimal128_34_digit_overflow",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": DECIMAL128_MAX_COEFFICIENT}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject Decimal128 with 34-digit max precision exceeding INT64_MAX",
    ),
    StageTestCase(
        "decimal128_extreme_positive_exponent",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": DECIMAL128_LARGE_EXPONENT}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject Decimal128 with extreme positive exponent",
    ),
    StageTestCase(
        "decimal128_int64_underflow",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": DECIMAL128_INT64_UNDERFLOW}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject Decimal128 below INT64_MIN",
    ),
]

SKIP_VALUE_ERROR_TESTS: list[StageTestCase] = (
    SKIP_NEGATIVE_VALUE_REJECTION_TESTS
    + SKIP_FRACTIONAL_VALUE_REJECTION_TESTS
    + SKIP_NON_FINITE_VALUE_REJECTION_TESTS
    + SKIP_OVERFLOW_REJECTION_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SKIP_VALUE_ERROR_TESTS))
def test_skip_value_errors(collection, test_case: StageTestCase):
    """Test $skip stage errors for invalid numeric values."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
