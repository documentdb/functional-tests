"""Tests for $out stage - timeseries value/range errors."""

from __future__ import annotations

from datetime import datetime

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.stages.out.utils.out_test_helpers import (
    OutTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    populate_collection,
)
from documentdb_tests.framework.assertions import (
    assertResult,
)
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    INVALID_OPTIONS_ERROR,
    MISSING_FIELD_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_HALF,
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ONE_AND_HALF,
    DECIMAL128_NEGATIVE_ZERO,
    DOUBLE_MAX,
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT32_OVERFLOW,
    INT32_UNDERFLOW,
)

# Property [Bucket Param Range Validation]: bucket parameter values outside
# the valid range (1 to 31536000) after numeric coercion to int32 produce
# error code 2.
OUT_BUCKET_PARAM_RANGE_ERROR_TESTS: list[OutTestCase] = [
    OutTestCase(
        "bucket_zero",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": 0,
                "bucketRoundingSeconds": 0,
            }
        },
        msg="$out should reject bucket parameter value 0 (below minimum)",
        error_code=BAD_VALUE_ERROR,
    ),
    OutTestCase(
        "bucket_negative",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": -1,
                "bucketRoundingSeconds": -1,
            }
        },
        msg="$out should reject negative bucket parameter values",
        error_code=BAD_VALUE_ERROR,
    ),
    OutTestCase(
        "bucket_above_max",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": 31_536_001,
                "bucketRoundingSeconds": 31_536_001,
            }
        },
        msg="$out should reject bucket parameter values above 31536000",
        error_code=BAD_VALUE_ERROR,
    ),
    OutTestCase(
        "bucket_float_truncates_to_zero",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": 0.5,
                "bucketRoundingSeconds": 0.5,
            }
        },
        msg="$out should reject float 0.5 (truncates to 0, below minimum)",
        error_code=BAD_VALUE_ERROR,
    ),
    OutTestCase(
        "bucket_float_negative_truncation",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": -1.5,
                "bucketRoundingSeconds": -1.5,
            }
        },
        msg="$out should reject float -1.5 (truncates to -1, below minimum)",
        error_code=BAD_VALUE_ERROR,
    ),
    OutTestCase(
        "bucket_float_nan",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": FLOAT_NAN,
                "bucketRoundingSeconds": FLOAT_NAN,
            }
        },
        msg="$out should reject float NaN (converts to 0, below minimum)",
        error_code=BAD_VALUE_ERROR,
    ),
    OutTestCase(
        "bucket_float_neg_zero",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": DOUBLE_NEGATIVE_ZERO,
                "bucketRoundingSeconds": DOUBLE_NEGATIVE_ZERO,
            }
        },
        msg="$out should reject float negative zero (converts to 0, below minimum)",
        error_code=BAD_VALUE_ERROR,
    ),
    OutTestCase(
        "bucket_float_inf",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": FLOAT_INFINITY,
                "bucketRoundingSeconds": FLOAT_INFINITY,
            }
        },
        msg="$out should reject float +Infinity (clamps to int32 max, above max range)",
        error_code=BAD_VALUE_ERROR,
    ),
    OutTestCase(
        "bucket_float_neg_inf",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": FLOAT_NEGATIVE_INFINITY,
                "bucketRoundingSeconds": FLOAT_NEGATIVE_INFINITY,
            }
        },
        msg="$out should reject float -Infinity (clamps to int32 min, below minimum)",
        error_code=BAD_VALUE_ERROR,
    ),
    OutTestCase(
        "bucket_float_subnormal",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": DOUBLE_MIN_SUBNORMAL,
                "bucketRoundingSeconds": DOUBLE_MIN_SUBNORMAL,
            }
        },
        msg="$out should reject float subnormal (truncates to 0, below minimum)",
        error_code=BAD_VALUE_ERROR,
    ),
    OutTestCase(
        "bucket_decimal128_neg_rounds",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": DECIMAL128_NEGATIVE_ONE_AND_HALF,
                "bucketRoundingSeconds": DECIMAL128_NEGATIVE_ONE_AND_HALF,
            }
        },
        msg="$out should reject Decimal128 -1.5 (rounds to -2, below minimum)",
        error_code=BAD_VALUE_ERROR,
    ),
    OutTestCase(
        "bucket_decimal128_half_to_zero",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": DECIMAL128_HALF,
                "bucketRoundingSeconds": DECIMAL128_HALF,
            }
        },
        msg="$out should reject Decimal128 0.5 (banker's rounds to 0, below minimum)",
        error_code=BAD_VALUE_ERROR,
    ),
    OutTestCase(
        "bucket_decimal128_nan",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": DECIMAL128_NAN,
                "bucketRoundingSeconds": DECIMAL128_NAN,
            }
        },
        msg="$out should reject Decimal128 NaN (converts to 0, below minimum)",
        error_code=BAD_VALUE_ERROR,
    ),
    OutTestCase(
        "bucket_decimal128_inf",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": DECIMAL128_INFINITY,
                "bucketRoundingSeconds": DECIMAL128_INFINITY,
            }
        },
        msg="$out should reject Decimal128 +Infinity (clamps to int32 max, above max range)",
        error_code=BAD_VALUE_ERROR,
    ),
    OutTestCase(
        "bucket_decimal128_neg_inf",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": DECIMAL128_NEGATIVE_INFINITY,
                "bucketRoundingSeconds": DECIMAL128_NEGATIVE_INFINITY,
            }
        },
        msg="$out should reject Decimal128 -Infinity (clamps to int32 min, below minimum)",
        error_code=BAD_VALUE_ERROR,
    ),
    OutTestCase(
        "bucket_decimal128_neg_zero",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": DECIMAL128_NEGATIVE_ZERO,
                "bucketRoundingSeconds": DECIMAL128_NEGATIVE_ZERO,
            }
        },
        msg="$out should reject Decimal128 -0 (converts to 0, below minimum)",
        error_code=BAD_VALUE_ERROR,
    ),
    OutTestCase(
        "bucket_int64_above_int32_max",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": Int64(INT32_OVERFLOW),
                "bucketRoundingSeconds": Int64(INT32_OVERFLOW),
            }
        },
        msg="$out should reject Int64 above int32 max (clamps to int32 max, above max range)",
        error_code=BAD_VALUE_ERROR,
    ),
    OutTestCase(
        "bucket_int64_int32_min",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": Int64(INT32_MIN),
                "bucketRoundingSeconds": Int64(INT32_MIN),
            }
        },
        msg="$out should reject Int64 at int32 min (below minimum)",
        error_code=BAD_VALUE_ERROR,
    ),
    OutTestCase(
        "bucket_int64_below_int32_min",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": Int64(INT32_UNDERFLOW),
                "bucketRoundingSeconds": Int64(INT32_UNDERFLOW),
            }
        },
        msg="$out should reject Int64 below int32 min (clamps to int32 min, below minimum)",
        error_code=BAD_VALUE_ERROR,
    ),
    OutTestCase(
        "bucket_float_max_safe_int",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": DOUBLE_MAX_SAFE_INTEGER,
                "bucketRoundingSeconds": DOUBLE_MAX_SAFE_INTEGER,
            }
        },
        msg="$out should reject float max safe integer (clamps to int32 max, above max range)",
        error_code=BAD_VALUE_ERROR,
    ),
    OutTestCase(
        "bucket_float_dbl_max",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": DOUBLE_MAX,
                "bucketRoundingSeconds": DOUBLE_MAX,
            }
        },
        msg="$out should reject float DBL_MAX (clamps to int32 max, above max range)",
        error_code=BAD_VALUE_ERROR,
    ),
    OutTestCase(
        "bucket_decimal128_large",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": Decimal128("1E+100"),
                "bucketRoundingSeconds": Decimal128("1E+100"),
            }
        },
        msg="$out should reject Decimal128 1E+100 (clamps to int32 max, above max range)",
        error_code=BAD_VALUE_ERROR,
    ),
    OutTestCase(
        "bucket_int32_max",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": INT32_MAX,
                "bucketRoundingSeconds": INT32_MAX,
            }
        },
        msg="$out should reject int32 max (above max range 31536000)",
        error_code=BAD_VALUE_ERROR,
    ),
    OutTestCase(
        "bucket_int32_min",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": INT32_MIN,
                "bucketRoundingSeconds": INT32_MIN,
            }
        },
        msg="$out should reject int32 min (below minimum)",
        error_code=BAD_VALUE_ERROR,
    ),
]

# Property [Null as Missing (Errors)]: null values for db, coll, and
# timeField are treated as missing rather than as type errors, and a null
# bucket parameter paired with a valid one produces an incomplete-pair

# Property [Timeseries Missing and Unknown Field Errors]: missing timeField
# inside the timeseries document produces a missing key error, and unknown
# fields inside the timeseries document produce an unrecognized field error.
OUT_TIMESERIES_MISSING_UNKNOWN_FIELD_ERROR_TESTS: list[OutTestCase] = [
    OutTestCase(
        "ts_missing_time_field_empty_ts",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": "target", "timeseries": {}}}],
        msg="$out should reject an empty timeseries document (missing timeField)",
        error_code=MISSING_FIELD_ERROR,
    ),
    OutTestCase(
        "ts_missing_time_field_with_meta",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"metaField": "m"},
                }
            }
        ],
        msg="$out should reject timeseries with metaField but missing timeField",
        error_code=MISSING_FIELD_ERROR,
    ),
    OutTestCase(
        "ts_unknown_field",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": "ts", "extra": "x"},
                }
            }
        ],
        msg="$out should reject unknown field inside timeseries document",
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
    ),
    OutTestCase(
        "ts_unknown_field_case_sensitive",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": "ts", "TimeField": "ts2"},
                }
            }
        ],
        msg="$out should reject case-variant field name inside timeseries as unknown",
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
    ),
]

# Property [Timeseries Granularity Errors]: invalid granularity strings
# produce error code 2 because validation is case-sensitive and only
# "seconds", "minutes", and "hours" are accepted.
OUT_TIMESERIES_GRANULARITY_ERROR_TESTS: list[OutTestCase] = [
    OutTestCase(
        "granularity_capitalized",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": "ts", "granularity": "Seconds"},
                }
            }
        ],
        msg="$out should reject capitalized 'Seconds' as an invalid granularity",
        error_code=BAD_VALUE_ERROR,
    ),
    OutTestCase(
        "granularity_all_caps",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": "ts", "granularity": "HOURS"},
                }
            }
        ],
        msg="$out should reject all-caps 'HOURS' as an invalid granularity",
        error_code=BAD_VALUE_ERROR,
    ),
    OutTestCase(
        "granularity_empty_string",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": "ts", "granularity": ""},
                }
            }
        ],
        msg="$out should reject empty string as an invalid granularity",
        error_code=BAD_VALUE_ERROR,
    ),
    OutTestCase(
        "granularity_arbitrary_string",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": "ts", "granularity": "invalid"},
                }
            }
        ],
        msg="$out should reject an arbitrary string as an invalid granularity",
        error_code=BAD_VALUE_ERROR,
    ),
    OutTestCase(
        "granularity_singular_form",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": "ts", "granularity": "second"},
                }
            }
        ],
        msg="$out should reject singular form 'second' as an invalid granularity",
        error_code=BAD_VALUE_ERROR,
    ),
]

# Property [Bucket Param Pairing Errors]: bucketMaxSpanSeconds and
# bucketRoundingSeconds must be specified together, must be equal, and
# cannot be combined with granularity.
OUT_BUCKET_PARAM_PAIRING_ERROR_TESTS: list[OutTestCase] = [
    OutTestCase(
        "bucket_max_without_rounding",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {
                        "timeField": "ts",
                        "bucketMaxSpanSeconds": 100,
                    },
                }
            }
        ],
        msg="$out should reject bucketMaxSpanSeconds without bucketRoundingSeconds",
        error_code=INVALID_OPTIONS_ERROR,
    ),
    OutTestCase(
        "bucket_rounding_without_max",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {
                        "timeField": "ts",
                        "bucketRoundingSeconds": 100,
                    },
                }
            }
        ],
        msg="$out should reject bucketRoundingSeconds without bucketMaxSpanSeconds",
        error_code=INVALID_OPTIONS_ERROR,
    ),
    OutTestCase(
        "bucket_params_not_equal",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {
                        "timeField": "ts",
                        "bucketMaxSpanSeconds": 100,
                        "bucketRoundingSeconds": 200,
                    },
                }
            }
        ],
        msg="$out should reject unequal bucketMaxSpanSeconds and bucketRoundingSeconds",
        error_code=INVALID_OPTIONS_ERROR,
    ),
    OutTestCase(
        "granularity_with_bucket_params",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {
                        "timeField": "ts",
                        "granularity": "seconds",
                        "bucketMaxSpanSeconds": 100,
                        "bucketRoundingSeconds": 100,
                    },
                }
            }
        ],
        msg="$out should reject granularity combined with bucket parameters",
        error_code=INVALID_OPTIONS_ERROR,
    ),
]

# Property [Timeseries Document Errors]: $out fails with error code 2
# when writing a document whose timeField value is not a valid datetime or
# when the timeField is missing entirely.
OUT_TIMESERIES_DOCUMENT_ERROR_TESTS: list[OutTestCase] = [
    OutTestCase(
        "ts_doc_non_date_time_field",
        docs=[{"_id": 1, "ts": "not_a_date", "v": 1}],
        out_spec={"timeseries": {"timeField": "ts"}},
        msg=(
            "$out should fail when writing a document with a non-date"
            " value in the timeField to a timeseries collection"
        ),
        error_code=BAD_VALUE_ERROR,
    ),
    OutTestCase(
        "ts_doc_missing_time_field",
        docs=[{"_id": 1, "v": 1}],
        out_spec={"timeseries": {"timeField": "ts"}},
        msg=(
            "$out should fail when writing a document missing the"
            " timeField entirely to a timeseries collection"
        ),
        error_code=BAD_VALUE_ERROR,
    ),
]


OUT_TIMESERIES_VALUE_ERROR_TESTS = (
    OUT_BUCKET_PARAM_RANGE_ERROR_TESTS
    + OUT_TIMESERIES_MISSING_UNKNOWN_FIELD_ERROR_TESTS
    + OUT_TIMESERIES_GRANULARITY_ERROR_TESTS
    + OUT_BUCKET_PARAM_PAIRING_ERROR_TESTS
    + OUT_TIMESERIES_DOCUMENT_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_TIMESERIES_VALUE_ERROR_TESTS))
def test_out_error(collection, test_case: OutTestCase):
    """Test $out rejects invalid configurations with the expected error code."""
    populate_collection(collection, test_case)
    if test_case.pipeline:
        pipeline = test_case.pipeline
    else:
        pipeline = [test_case.build_out_stage(collection)]
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}},
    )

    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)
