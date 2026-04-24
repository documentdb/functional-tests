"""Tests for $limit error handling and validation."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    LIMIT_INVALID_ARGUMENT_ERROR,
    LIMIT_NOT_POSITIVE_ERROR,
    PIPELINE_STAGE_EXTRA_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_HALF,
    DECIMAL128_INFINITY,
    DECIMAL128_INT64_OVERFLOW,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_SMALL_EXPONENT,
    DECIMAL128_ZERO,
    DOUBLE_FROM_INT64_MAX,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    DOUBLE_NEGATIVE_HALF,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ONE_AND_HALF,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
    INT64_ZERO,
)

# Property [Zero Value Error]: zero in any numeric type produces the
# LIMIT_NOT_POSITIVE_ERROR.
LIMIT_ZERO_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "zero_int32",
        pipeline=[{"$limit": 0}],
        error_code=LIMIT_NOT_POSITIVE_ERROR,
        msg="$limit should reject int32 zero",
    ),
    StageTestCase(
        "zero_int64",
        pipeline=[{"$limit": INT64_ZERO}],
        error_code=LIMIT_NOT_POSITIVE_ERROR,
        msg="$limit should reject int64 zero",
    ),
    StageTestCase(
        "zero_double",
        pipeline=[{"$limit": DOUBLE_ZERO}],
        error_code=LIMIT_NOT_POSITIVE_ERROR,
        msg="$limit should reject double zero",
    ),
    StageTestCase(
        "zero_decimal128",
        pipeline=[{"$limit": DECIMAL128_ZERO}],
        error_code=LIMIT_NOT_POSITIVE_ERROR,
        msg="$limit should reject Decimal128 zero",
    ),
    StageTestCase(
        "negative_zero_double",
        pipeline=[{"$limit": DOUBLE_NEGATIVE_ZERO}],
        error_code=LIMIT_NOT_POSITIVE_ERROR,
        msg="$limit should reject double -0.0 as zero",
    ),
    StageTestCase(
        "negative_zero_decimal128",
        pipeline=[{"$limit": DECIMAL128_NEGATIVE_ZERO}],
        error_code=LIMIT_NOT_POSITIVE_ERROR,
        msg="$limit should reject Decimal128 -0 as zero",
    ),
]

# Property [Non-Numeric Type Error]: all non-numeric BSON types produce the
# LIMIT_INVALID_ARGUMENT_ERROR, including arrays and expression-like objects.
LIMIT_NON_NUMERIC_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "string",
        pipeline=[{"$limit": "abc"}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject string",
    ),
    StageTestCase(
        "bool_true",
        pipeline=[{"$limit": True}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject bool true",
    ),
    StageTestCase(
        "bool_false",
        pipeline=[{"$limit": False}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject bool false",
    ),
    StageTestCase(
        "null",
        pipeline=[{"$limit": None}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject null",
    ),
    StageTestCase(
        "objectid",
        pipeline=[{"$limit": ObjectId()}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject ObjectId",
    ),
    StageTestCase(
        "datetime",
        pipeline=[{"$limit": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject datetime",
    ),
    StageTestCase(
        "timestamp",
        pipeline=[{"$limit": Timestamp(100, 1)}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject Timestamp",
    ),
    StageTestCase(
        "binary",
        pipeline=[{"$limit": Binary(b"\x01")}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject Binary",
    ),
    StageTestCase(
        "regex",
        pipeline=[{"$limit": Regex("^abc")}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject Regex",
    ),
    StageTestCase(
        "code",
        pipeline=[{"$limit": Code("function(){}")}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject Code",
    ),
    StageTestCase(
        "code_with_scope",
        pipeline=[{"$limit": Code("function(){}", {})}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject CodeWithScope",
    ),
    StageTestCase(
        "minkey",
        pipeline=[{"$limit": MinKey()}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject MinKey",
    ),
    StageTestCase(
        "maxkey",
        pipeline=[{"$limit": MaxKey()}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject MaxKey",
    ),
    StageTestCase(
        "empty_array",
        pipeline=[{"$limit": []}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject empty array",
    ),
    StageTestCase(
        "single_element_array",
        pipeline=[{"$limit": [1]}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject single-element array",
    ),
    StageTestCase(
        "nested_array",
        pipeline=[{"$limit": [[1]]}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject nested array",
    ),
    StageTestCase(
        "empty_object",
        pipeline=[{"$limit": {}}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject empty object",
    ),
    StageTestCase(
        "expression_like_object",
        pipeline=[{"$limit": {"$add": [1, 2]}}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject expression-like objects without evaluating",
    ),
    StageTestCase(
        "literal_object",
        pipeline=[{"$limit": {"$literal": 5}}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject $literal objects without evaluating",
    ),
]

# Property [Fractional Value Error]: fractional double and Decimal128 values
# produce the LIMIT_INVALID_ARGUMENT_ERROR.
LIMIT_FRACTIONAL_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "fractional_double_half",
        pipeline=[{"$limit": 0.5}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject fractional double 0.5",
    ),
    StageTestCase(
        "fractional_double_one_and_half",
        pipeline=[{"$limit": DOUBLE_ONE_AND_HALF}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject fractional double 1.5",
    ),
    StageTestCase(
        "fractional_double_two_and_half",
        pipeline=[{"$limit": 2.5}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject fractional double 2.5",
    ),
    StageTestCase(
        "fractional_decimal128_half",
        pipeline=[{"$limit": DECIMAL128_HALF}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject fractional Decimal128 0.5",
    ),
    StageTestCase(
        "fractional_decimal128_one_and_half",
        pipeline=[{"$limit": DECIMAL128_ONE_AND_HALF}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject fractional Decimal128 1.5",
    ),
    StageTestCase(
        "subnormal_double",
        pipeline=[{"$limit": DOUBLE_MIN_SUBNORMAL}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject subnormal double",
    ),
    StageTestCase(
        "decimal128_fractional_exponent",
        pipeline=[{"$limit": Decimal128("5001E-3")}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject Decimal128 exponent resolving to fractional",
    ),
    StageTestCase(
        "decimal128_small_exponent",
        pipeline=[{"$limit": DECIMAL128_SMALL_EXPONENT}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject Decimal128 with extreme negative exponent",
    ),
]

# Property [Non-Finite Value Error]: NaN and infinity in double and Decimal128
# produce the LIMIT_INVALID_ARGUMENT_ERROR.
LIMIT_NON_FINITE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "nan_double",
        pipeline=[{"$limit": FLOAT_NAN}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject double NaN",
    ),
    StageTestCase(
        "nan_decimal128",
        pipeline=[{"$limit": DECIMAL128_NAN}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject Decimal128 NaN",
    ),
    StageTestCase(
        "neg_nan_double",
        pipeline=[{"$limit": FLOAT_NEGATIVE_NAN}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject double negative NaN",
    ),
    StageTestCase(
        "neg_nan_decimal128",
        pipeline=[{"$limit": DECIMAL128_NEGATIVE_NAN}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject Decimal128 negative NaN",
    ),
    StageTestCase(
        "inf_double",
        pipeline=[{"$limit": FLOAT_INFINITY}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject double positive infinity",
    ),
    StageTestCase(
        "neg_inf_double",
        pipeline=[{"$limit": FLOAT_NEGATIVE_INFINITY}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject double negative infinity",
    ),
    StageTestCase(
        "inf_decimal128",
        pipeline=[{"$limit": DECIMAL128_INFINITY}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject Decimal128 positive infinity",
    ),
    StageTestCase(
        "neg_inf_decimal128",
        pipeline=[{"$limit": DECIMAL128_NEGATIVE_INFINITY}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject Decimal128 negative infinity",
    ),
]

# Property [Overflow Error]: double and Decimal128 values exceeding the int64
# range produce the LIMIT_INVALID_ARGUMENT_ERROR.
LIMIT_OVERFLOW_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "overflow_double_2_pow_63",
        pipeline=[{"$limit": DOUBLE_FROM_INT64_MAX}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject double equal to 2^63",
    ),
    StageTestCase(
        "overflow_double_1e308",
        pipeline=[{"$limit": DOUBLE_NEAR_MAX}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject double 1e308",
    ),
    StageTestCase(
        "overflow_decimal128",
        pipeline=[{"$limit": DECIMAL128_INT64_OVERFLOW}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject Decimal128 exceeding int64 range",
    ),
    StageTestCase(
        "overflow_decimal128_large_exponent",
        pipeline=[{"$limit": DECIMAL128_LARGE_EXPONENT}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject Decimal128 with extreme positive exponent",
    ),
]

# Property [Negative Value Error]: negative whole-number values produce the
# LIMIT_INVALID_ARGUMENT_ERROR.
LIMIT_NEGATIVE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "negative_int32",
        pipeline=[{"$limit": -1}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject negative int32",
    ),
    StageTestCase(
        "negative_int64",
        pipeline=[{"$limit": Int64(-1)}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject negative int64",
    ),
    StageTestCase(
        "negative_decimal128",
        pipeline=[{"$limit": Decimal128("-1")}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject negative Decimal128",
    ),
    StageTestCase(
        "negative_fractional_double",
        pipeline=[{"$limit": DOUBLE_NEGATIVE_HALF}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject negative fractional double",
    ),
]

# Property [Stage Specification Shape Error]: extra keys in the $limit stage
# document produce the PIPELINE_STAGE_EXTRA_FIELD_ERROR.
LIMIT_SHAPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "extra_key_operator",
        pipeline=[{"$limit": 5, "$skip": 2}],
        error_code=PIPELINE_STAGE_EXTRA_FIELD_ERROR,
        msg="$limit stage with extra operator key should produce error",
    ),
    StageTestCase(
        "extra_key_non_operator",
        pipeline=[{"$limit": 5, "foo": 1}],
        error_code=PIPELINE_STAGE_EXTRA_FIELD_ERROR,
        msg="$limit stage with extra non-operator key should produce error",
    ),
]

# Property [Errors on Non-Existent Collection]: every validation error fires
# even when the collection does not exist, confirming that the server rejects
# invalid $limit parameters without requiring any input documents.
LIMIT_NONEXISTENT_COLLECTION_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "timing_invalid_argument_nonexistent_collection",
        docs=None,
        pipeline=[{"$limit": "abc"}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit invalid argument error should fire on a non-existent collection",
    ),
    StageTestCase(
        "timing_not_positive_nonexistent_collection",
        docs=None,
        pipeline=[{"$limit": 0}],
        error_code=LIMIT_NOT_POSITIVE_ERROR,
        msg="$limit not-positive error should fire on a non-existent collection",
    ),
    StageTestCase(
        "timing_extra_field_nonexistent_collection",
        docs=None,
        pipeline=[{"$limit": 5, "extra": 1}],
        error_code=PIPELINE_STAGE_EXTRA_FIELD_ERROR,
        msg="$limit extra field error should fire on a non-existent collection",
    ),
]

# Property [Errors on Empty Collection]: every validation error fires even
# when the collection is empty, confirming that the server rejects invalid
# $limit parameters without requiring any input documents.
LIMIT_EMPTY_COLLECTION_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "timing_invalid_argument_empty_collection",
        docs=[],
        pipeline=[{"$limit": "abc"}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit invalid argument error should fire on empty collection",
    ),
    StageTestCase(
        "timing_not_positive_empty_collection",
        docs=[],
        pipeline=[{"$limit": 0}],
        error_code=LIMIT_NOT_POSITIVE_ERROR,
        msg="$limit not-positive error should fire on empty collection",
    ),
    StageTestCase(
        "timing_extra_field_empty_collection",
        docs=[],
        pipeline=[{"$limit": 5, "extra": 1}],
        error_code=PIPELINE_STAGE_EXTRA_FIELD_ERROR,
        msg="$limit extra field error should fire on empty collection",
    ),
]

# Property [Cross-Stage Error Precedence]: when multiple stages have invalid
# values, the first invalid stage by position produces the error.
LIMIT_PRECEDENCE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "first_zero_then_negative",
        pipeline=[{"$limit": 0}, {"$limit": -1}],
        error_code=LIMIT_NOT_POSITIVE_ERROR,
        msg="First invalid stage (zero) should produce its error code",
    ),
    StageTestCase(
        "first_negative_then_zero",
        pipeline=[{"$limit": -1}, {"$limit": 0}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="First invalid stage (negative) should produce its error code",
    ),
]

LIMIT_ERROR_TESTS = (
    LIMIT_ZERO_ERROR_TESTS
    + LIMIT_NON_NUMERIC_ERROR_TESTS
    + LIMIT_FRACTIONAL_ERROR_TESTS
    + LIMIT_NON_FINITE_ERROR_TESTS
    + LIMIT_OVERFLOW_ERROR_TESTS
    + LIMIT_NEGATIVE_ERROR_TESTS
    + LIMIT_SHAPE_ERROR_TESTS
    + LIMIT_NONEXISTENT_COLLECTION_ERROR_TESTS
    + LIMIT_EMPTY_COLLECTION_ERROR_TESTS
    + LIMIT_PRECEDENCE_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LIMIT_ERROR_TESTS))
def test_limit_errors(collection, test_case: StageTestCase):
    """Test $limit validation and error handling."""
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
