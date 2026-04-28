"""Tests for $sample stage size value errors."""

from __future__ import annotations

from datetime import datetime

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    SAMPLE_SIZE_MISSING_ERROR,
    SAMPLE_SIZE_NOT_NUMERIC_ERROR,
    SAMPLE_SIZE_NOT_POSITIVE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_HALF,
    DECIMAL128_JUST_BELOW_HALF,
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_SMALL_EXPONENT,
    DECIMAL128_ZERO,
    DOUBLE_MIN_NORMAL,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT64_ZERO,
)

# Property [Null and Missing Errors]: null and missing size values are
# rejected with distinct error codes.
SAMPLE_NULL_MISSING_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "null_size",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": None}}],
        error_code=SAMPLE_SIZE_NOT_NUMERIC_ERROR,
        msg="$sample should reject null size as non-numeric",
    ),
    StageTestCase(
        "missing_size",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {}}],
        error_code=SAMPLE_SIZE_MISSING_ERROR,
        msg="$sample should reject missing size field",
    ),
]

# Property [Type Strictness]: all non-numeric BSON types for size produce an
# error, including arrays and expression-like subdocuments which are not
# unwrapped or evaluated.
SAMPLE_TYPE_STRICTNESS_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "type_string",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": "3"}}],
        error_code=SAMPLE_SIZE_NOT_NUMERIC_ERROR,
        msg="$sample should reject string size",
    ),
    StageTestCase(
        "type_bool_true",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": True}}],
        error_code=SAMPLE_SIZE_NOT_NUMERIC_ERROR,
        msg="$sample should reject bool True as size",
    ),
    StageTestCase(
        "type_bool_false",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": False}}],
        error_code=SAMPLE_SIZE_NOT_NUMERIC_ERROR,
        msg="$sample should reject bool False as size",
    ),
    StageTestCase(
        "type_array",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": [5]}}],
        error_code=SAMPLE_SIZE_NOT_NUMERIC_ERROR,
        msg="$sample should reject array [5] without unwrapping",
    ),
    StageTestCase(
        "type_object",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": {"a": 1}}}],
        error_code=SAMPLE_SIZE_NOT_NUMERIC_ERROR,
        msg="$sample should reject plain object as size",
    ),
    StageTestCase(
        "type_objectid",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": ObjectId()}}],
        error_code=SAMPLE_SIZE_NOT_NUMERIC_ERROR,
        msg="$sample should reject ObjectId as size",
    ),
    StageTestCase(
        "type_datetime",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": datetime(2023, 1, 1)}}],
        error_code=SAMPLE_SIZE_NOT_NUMERIC_ERROR,
        msg="$sample should reject datetime as size",
    ),
    StageTestCase(
        "type_timestamp",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": Timestamp(1, 1)}}],
        error_code=SAMPLE_SIZE_NOT_NUMERIC_ERROR,
        msg="$sample should reject Timestamp as size",
    ),
    StageTestCase(
        "type_binary",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": Binary(b"\x01\x02")}}],
        error_code=SAMPLE_SIZE_NOT_NUMERIC_ERROR,
        msg="$sample should reject Binary as size",
    ),
    StageTestCase(
        "type_regex",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": Regex("abc")}}],
        error_code=SAMPLE_SIZE_NOT_NUMERIC_ERROR,
        msg="$sample should reject Regex as size",
    ),
    StageTestCase(
        "type_code",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": Code("function(){}")}}],
        error_code=SAMPLE_SIZE_NOT_NUMERIC_ERROR,
        msg="$sample should reject Code as size",
    ),
    StageTestCase(
        "type_code_with_scope",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": Code("function(){}", {"x": 1})}}],
        error_code=SAMPLE_SIZE_NOT_NUMERIC_ERROR,
        msg="$sample should reject CodeWithScope as size",
    ),
    StageTestCase(
        "type_minkey",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": MinKey()}}],
        error_code=SAMPLE_SIZE_NOT_NUMERIC_ERROR,
        msg="$sample should reject MinKey as size",
    ),
    StageTestCase(
        "type_maxkey",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": MaxKey()}}],
        error_code=SAMPLE_SIZE_NOT_NUMERIC_ERROR,
        msg="$sample should reject MaxKey as size",
    ),
    StageTestCase(
        "type_expression_subdocument",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": {"$add": [1, 2]}}}],
        error_code=SAMPLE_SIZE_NOT_NUMERIC_ERROR,
        msg="$sample should not evaluate expression subdocuments as size",
    ),
    StageTestCase(
        "type_field_path_string",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": "$fieldName"}}],
        error_code=SAMPLE_SIZE_NOT_NUMERIC_ERROR,
        msg="$sample should not evaluate field path strings as size",
    ),
]

# Property [Zero Value Errors]: zero in any numeric representation produces
# a not-positive error.
SAMPLE_ZERO_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "zero_int32",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": 0}}],
        error_code=SAMPLE_SIZE_NOT_POSITIVE_ERROR,
        msg="$sample should reject int32 zero",
    ),
    StageTestCase(
        "zero_int64",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": INT64_ZERO}}],
        error_code=SAMPLE_SIZE_NOT_POSITIVE_ERROR,
        msg="$sample should reject int64 zero",
    ),
    StageTestCase(
        "zero_double",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": DOUBLE_ZERO}}],
        error_code=SAMPLE_SIZE_NOT_POSITIVE_ERROR,
        msg="$sample should reject double 0.0",
    ),
    StageTestCase(
        "zero_negative_double",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": DOUBLE_NEGATIVE_ZERO}}],
        error_code=SAMPLE_SIZE_NOT_POSITIVE_ERROR,
        msg="$sample should reject double -0.0",
    ),
    StageTestCase(
        "zero_decimal128",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": DECIMAL128_ZERO}}],
        error_code=SAMPLE_SIZE_NOT_POSITIVE_ERROR,
        msg="$sample should reject Decimal128('0')",
    ),
    StageTestCase(
        "zero_decimal128_neg",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": DECIMAL128_NEGATIVE_ZERO}}],
        error_code=SAMPLE_SIZE_NOT_POSITIVE_ERROR,
        msg="$sample should reject Decimal128('-0')",
    ),
    StageTestCase(
        "zero_decimal128_neg_exp_neg",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": Decimal128("-0E-10")}}],
        error_code=SAMPLE_SIZE_NOT_POSITIVE_ERROR,
        msg="$sample should reject Decimal128('-0E-10')",
    ),
    StageTestCase(
        "zero_decimal128_neg_exp_pos",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": Decimal128("-0E+10")}}],
        error_code=SAMPLE_SIZE_NOT_POSITIVE_ERROR,
        msg="$sample should reject Decimal128('-0E+10')",
    ),
]

# Property [Negative Value Errors]: all negative numeric values produce a
# not-positive error.
SAMPLE_NEGATIVE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "negative_int32",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": -1}}],
        error_code=SAMPLE_SIZE_NOT_POSITIVE_ERROR,
        msg="$sample should reject negative int32",
    ),
    StageTestCase(
        "negative_int64",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": Int64(-100)}}],
        error_code=SAMPLE_SIZE_NOT_POSITIVE_ERROR,
        msg="$sample should reject negative int64",
    ),
    StageTestCase(
        "negative_double",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": -1.5}}],
        error_code=SAMPLE_SIZE_NOT_POSITIVE_ERROR,
        msg="$sample should reject negative double",
    ),
    StageTestCase(
        "negative_decimal128",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": Decimal128("-1")}}],
        error_code=SAMPLE_SIZE_NOT_POSITIVE_ERROR,
        msg="$sample should reject negative Decimal128",
    ),
]

# Property [NaN and Negative Infinity Errors]: NaN and negative infinity
# produce a not-positive error regardless of numeric type.
SAMPLE_NAN_NEG_INF_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "nan_double",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": FLOAT_NAN}}],
        error_code=SAMPLE_SIZE_NOT_POSITIVE_ERROR,
        msg="$sample should reject double NaN",
    ),
    StageTestCase(
        "nan_decimal128",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": DECIMAL128_NAN}}],
        error_code=SAMPLE_SIZE_NOT_POSITIVE_ERROR,
        msg="$sample should reject Decimal128 NaN",
    ),
    StageTestCase(
        "neg_inf_double",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": FLOAT_NEGATIVE_INFINITY}}],
        error_code=SAMPLE_SIZE_NOT_POSITIVE_ERROR,
        msg="$sample should reject double negative infinity",
    ),
    StageTestCase(
        "neg_inf_decimal128",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": DECIMAL128_NEGATIVE_INFINITY}}],
        error_code=SAMPLE_SIZE_NOT_POSITIVE_ERROR,
        msg="$sample should reject Decimal128 negative infinity",
    ),
]

# Property [Fractional Round to Zero]: positive fractional values that
# coerce to an effective size of zero produce a not-positive error.
SAMPLE_FRACTIONAL_ROUND_TO_ZERO_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "frac_double_0_5",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": 0.5}}],
        error_code=SAMPLE_SIZE_NOT_POSITIVE_ERROR,
        msg="$sample should reject double 0.5 (floors to 0)",
    ),
    StageTestCase(
        "frac_double_subnormal_min",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": DOUBLE_MIN_SUBNORMAL}}],
        error_code=SAMPLE_SIZE_NOT_POSITIVE_ERROR,
        msg="$sample should reject subnormal double (floors to 0)",
    ),
    StageTestCase(
        "frac_double_min_normal",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": DOUBLE_MIN_NORMAL}}],
        error_code=SAMPLE_SIZE_NOT_POSITIVE_ERROR,
        msg="$sample should reject smallest normal double (floors to 0)",
    ),
    StageTestCase(
        "frac_decimal128_half_bankers",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": DECIMAL128_HALF}}],
        error_code=SAMPLE_SIZE_NOT_POSITIVE_ERROR,
        msg="$sample should reject Decimal128 0.5 (banker's rounds to 0)",
    ),
    StageTestCase(
        "frac_decimal128_just_below_half",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": DECIMAL128_JUST_BELOW_HALF}}],
        error_code=SAMPLE_SIZE_NOT_POSITIVE_ERROR,
        msg="$sample should reject Decimal128 just below 0.5 (rounds to 0)",
    ),
    StageTestCase(
        "frac_decimal128_small_exponent",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": DECIMAL128_SMALL_EXPONENT}}],
        error_code=SAMPLE_SIZE_NOT_POSITIVE_ERROR,
        msg="$sample should reject Decimal128 with a small exponent (rounds to 0)",
    ),
    StageTestCase(
        "frac_decimal128_min_positive",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": DECIMAL128_MIN_POSITIVE}}],
        error_code=SAMPLE_SIZE_NOT_POSITIVE_ERROR,
        msg="$sample should reject the smallest positive Decimal128 (rounds to 0)",
    ),
]

SAMPLE_SIZE_ERROR_TESTS = (
    SAMPLE_NULL_MISSING_ERROR_TESTS
    + SAMPLE_TYPE_STRICTNESS_ERROR_TESTS
    + SAMPLE_ZERO_ERROR_TESTS
    + SAMPLE_NEGATIVE_ERROR_TESTS
    + SAMPLE_NAN_NEG_INF_ERROR_TESTS
    + SAMPLE_FRACTIONAL_ROUND_TO_ZERO_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SAMPLE_SIZE_ERROR_TESTS))
def test_sample_size_errors(collection, test_case: StageTestCase):
    """Test $sample stage size value errors."""
    if test_case.setup:
        test_case.setup(collection)
    if test_case.docs:
        collection.insert_many(test_case.docs)
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
        ignore_doc_order=True,
    )
