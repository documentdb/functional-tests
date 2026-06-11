"""Tests for the create command timeseries validation behavior."""

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

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    INVALID_OPTIONS_ERROR,
    MISSING_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
)

# Property [Timeseries Type Strictness]: non-object types for the timeseries
# field produce TYPE_MISMATCH_ERROR.
CREATE_TIMESERIES_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id=f"timeseries_non_object_{label}",
        command=lambda ctx, val=val: {
            "create": f"{ctx.collection}_custom",
            "timeseries": val,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"Non-object ({label}) timeseries should fail",
    )
    for label, val in [
        ("string", "not_object"),
        ("int", 123),
        ("array", [{"timeField": "ts"}]),
        ("bool", True),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("binary", Binary(b"x")),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("regex", Regex("x")),
        ("code", Code("f()")),
        ("code_with_scope", Code("f()", {"x": 1})),
        ("timestamp", Timestamp(0, 0)),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Timeseries TimeField Validation]: missing, null, non-string,
# dotted, and null-byte timeField values produce their respective errors.
CREATE_TIMESERIES_TIMEFIELD_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="timeseries_missing_timefield",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {},
        },
        error_code=MISSING_FIELD_ERROR,
        msg="Missing timeField should fail",
    ),
    *[
        CommandTestCase(
            id=f"timeseries_non_string_timefield_{tid}",
            command=lambda ctx, v=val: {
                "create": f"{ctx.collection}_custom",
                "timeseries": {"timeField": v},
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"Non-string timeField ({tid}) should fail",
        )
        for tid, val in [
            ("int", 123),
            ("int64", Int64(1)),
            ("double", 3.14),
            ("decimal128", Decimal128("1")),
            ("bool", True),
            ("array", [1]),
            ("document", {"x": 1}),
            ("binary", Binary(b"x")),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("regex", Regex("x")),
            ("code", Code("f()")),
            ("code_with_scope", Code("f()", {"x": 1})),
            ("timestamp", Timestamp(0, 0)),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    CommandTestCase(
        id="timeseries_null_timefield",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": None},
        },
        error_code=MISSING_FIELD_ERROR,
        msg="Null timeField treated as missing should fail",
    ),
    CommandTestCase(
        id="timeseries_dots_in_timefield",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "a.b"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Dots in timeField should fail",
    ),
    CommandTestCase(
        id="timeseries_null_bytes_in_timefield",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "a\x00b"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="Null bytes in timeField should fail",
    ),
]

# Property [Timeseries MetaField Type Validation]: non-string types for
# metaField produce TYPE_MISMATCH_ERROR.
CREATE_TIMESERIES_METAFIELD_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id=f"timeseries_non_string_metafield_{tid}",
        command=lambda ctx, v=val: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts", "metaField": v},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"Non-string metaField ({tid}) should fail",
    )
    for tid, val in [
        ("int", 123),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("bool", True),
        ("array", [1]),
        ("document", {"x": 1}),
        ("binary", Binary(b"x")),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("regex", Regex("x")),
        ("code", Code("f()")),
        ("code_with_scope", Code("f()", {"x": 1})),
        ("timestamp", Timestamp(0, 0)),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Timeseries MetaField Validation]: dotted, null-byte, _id, and
# metaField equal to timeField produce their respective errors.
CREATE_TIMESERIES_METAFIELD_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="timeseries_dots_in_metafield",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts", "metaField": "a.b"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Dots in metaField should fail",
    ),
    CommandTestCase(
        id="timeseries_null_bytes_in_metafield",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts", "metaField": "a\x00b"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="Null bytes in metaField should fail",
    ),
    CommandTestCase(
        id="timeseries_metafield_is_id",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts", "metaField": "_id"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="metaField = '_id' should fail",
    ),
    CommandTestCase(
        id="timeseries_metafield_equals_timefield",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts", "metaField": "ts"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="metaField = timeField value should fail (case-sensitive)",
    ),
]

# Property [Timeseries Granularity Validation]: invalid and non-string
# granularity values produce their respective errors.
CREATE_TIMESERIES_GRANULARITY_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="timeseries_invalid_granularity_string",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts", "granularity": "invalid"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="Invalid granularity string should fail",
    ),
    *[
        CommandTestCase(
            id=f"timeseries_non_string_granularity_{tid}",
            command=lambda ctx, v=val: {
                "create": f"{ctx.collection}_custom",
                "timeseries": {"timeField": "ts", "granularity": v},
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"Non-string granularity ({tid}) should fail",
        )
        for tid, val in [
            ("int", 123),
            ("int64", Int64(1)),
            ("double", 3.14),
            ("decimal128", Decimal128("1")),
            ("bool", True),
            ("array", [1]),
            ("document", {"x": 1}),
            ("binary", Binary(b"x")),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("regex", Regex("x")),
            ("code", Code("f()")),
            ("code_with_scope", Code("f()", {"x": 1})),
            ("timestamp", Timestamp(0, 0)),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
]

# Property [Timeseries Bucket Field Type Strictness]: non-numeric types for
# bucketMaxSpanSeconds and bucketRoundingSeconds produce TYPE_MISMATCH_ERROR.
CREATE_TIMESERIES_BUCKET_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            id=f"timeseries_bucket_max_span_non_numeric_{tid}",
            command=lambda ctx, v=val: {
                "create": f"{ctx.collection}_custom",
                "timeseries": {
                    "timeField": "ts",
                    "bucketMaxSpanSeconds": v,
                    "bucketRoundingSeconds": 300,
                },
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"Non-numeric bucketMaxSpanSeconds ({tid}) should fail",
        )
        for tid, val in [
            ("string", "300"),
            ("bool", True),
            ("array", [300]),
            ("document", {"x": 1}),
            ("binary", Binary(b"x")),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("regex", Regex("x")),
            ("code", Code("f()")),
            ("code_with_scope", Code("f()", {"x": 1})),
            ("timestamp", Timestamp(0, 0)),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    *[
        CommandTestCase(
            id=f"timeseries_bucket_rounding_non_numeric_{tid}",
            command=lambda ctx, v=val: {
                "create": f"{ctx.collection}_custom",
                "timeseries": {
                    "timeField": "ts",
                    "bucketMaxSpanSeconds": 300,
                    "bucketRoundingSeconds": v,
                },
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"Non-numeric bucketRoundingSeconds ({tid}) should fail",
        )
        for tid, val in [
            ("string", "300"),
            ("bool", True),
            ("array", [300]),
            ("document", {"x": 1}),
            ("binary", Binary(b"x")),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("regex", Regex("x")),
            ("code", Code("f()")),
            ("code_with_scope", Code("f()", {"x": 1})),
            ("timestamp", Timestamp(0, 0)),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
]

# Property [Timeseries Bucket Pairing and Value Rejection]: bucket fields must
# be paired, must match, cannot combine with granularity, and values outside
# [1, 31536000] (including NaN and Infinity) produce errors.
CREATE_TIMESERIES_BUCKET_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="timeseries_bucket_rounding_without_max",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts", "bucketRoundingSeconds": 300},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="bucketRoundingSeconds without bucketMaxSpanSeconds should fail",
    ),
    CommandTestCase(
        id="timeseries_bucket_max_without_rounding",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts", "bucketMaxSpanSeconds": 300},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="bucketMaxSpanSeconds without bucketRoundingSeconds should fail",
    ),
    CommandTestCase(
        id="timeseries_bucket_max_ne_rounding",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": 300,
                "bucketRoundingSeconds": 600,
            },
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="bucketMaxSpanSeconds != bucketRoundingSeconds should fail",
    ),
    CommandTestCase(
        id="timeseries_bucket_rounding_with_granularity",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {
                "timeField": "ts",
                "granularity": "seconds",
                "bucketRoundingSeconds": 300,
                "bucketMaxSpanSeconds": 300,
            },
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="bucketRoundingSeconds + granularity are mutually exclusive",
    ),
    CommandTestCase(
        id="timeseries_bucket_value_zero",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": 0,
                "bucketRoundingSeconds": 0,
            },
        },
        error_code=BAD_VALUE_ERROR,
        msg="Bucket value 0 (below range) should fail",
    ),
    CommandTestCase(
        id="timeseries_bucket_value_negative",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": -1,
                "bucketRoundingSeconds": -1,
            },
        },
        error_code=BAD_VALUE_ERROR,
        msg="Negative bucket value should fail",
    ),
    CommandTestCase(
        id="timeseries_bucket_value_exceeds_max",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": 31_536_001,
                "bucketRoundingSeconds": 31_536_001,
            },
        },
        error_code=BAD_VALUE_ERROR,
        msg="Bucket value > 31536000 should fail",
    ),
    CommandTestCase(
        id="timeseries_bucket_nan",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": FLOAT_NAN,
                "bucketRoundingSeconds": FLOAT_NAN,
            },
        },
        error_code=BAD_VALUE_ERROR,
        msg="NaN bucket value coerces to 0, which is below range",
    ),
    CommandTestCase(
        id="timeseries_bucket_negative_nan",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": FLOAT_NEGATIVE_NAN,
                "bucketRoundingSeconds": FLOAT_NEGATIVE_NAN,
            },
        },
        error_code=BAD_VALUE_ERROR,
        msg="-NaN bucket value coerces to 0, which is below range",
    ),
    CommandTestCase(
        id="timeseries_bucket_decimal128_nan",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": DECIMAL128_NAN,
                "bucketRoundingSeconds": DECIMAL128_NAN,
            },
        },
        error_code=BAD_VALUE_ERROR,
        msg="Decimal128 NaN bucket value coerces to 0, which is below range",
    ),
    CommandTestCase(
        id="timeseries_bucket_decimal128_negative_nan",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": DECIMAL128_NEGATIVE_NAN,
                "bucketRoundingSeconds": DECIMAL128_NEGATIVE_NAN,
            },
        },
        error_code=BAD_VALUE_ERROR,
        msg="Decimal128 -NaN bucket value coerces to 0, which is below range",
    ),
    CommandTestCase(
        id="timeseries_bucket_infinity",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": FLOAT_INFINITY,
                "bucketRoundingSeconds": FLOAT_INFINITY,
            },
        },
        error_code=BAD_VALUE_ERROR,
        msg="Infinity bucket value coerces to INT32_MAX, which exceeds range",
    ),
    CommandTestCase(
        id="timeseries_bucket_negative_infinity",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": FLOAT_NEGATIVE_INFINITY,
                "bucketRoundingSeconds": FLOAT_NEGATIVE_INFINITY,
            },
        },
        error_code=BAD_VALUE_ERROR,
        msg="-Infinity bucket value coerces to negative, which is below range",
    ),
    CommandTestCase(
        id="timeseries_bucket_decimal128_infinity",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": DECIMAL128_INFINITY,
                "bucketRoundingSeconds": DECIMAL128_INFINITY,
            },
        },
        error_code=BAD_VALUE_ERROR,
        msg="Decimal128 Infinity bucket value exceeds range",
    ),
    CommandTestCase(
        id="timeseries_bucket_decimal128_negative_infinity",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": DECIMAL128_NEGATIVE_INFINITY,
                "bucketRoundingSeconds": DECIMAL128_NEGATIVE_INFINITY,
            },
        },
        error_code=BAD_VALUE_ERROR,
        msg="Decimal128 -Infinity bucket value is below range",
    ),
]

# Property [Timeseries Unknown Sub-Fields]: unknown fields in the timeseries
# document produce UNRECOGNIZED_COMMAND_FIELD_ERROR.
CREATE_TIMESERIES_UNKNOWN_FIELD_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="timeseries_unknown_subfield",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts", "unknownField": "x"},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Unknown sub-fields in timeseries document should fail",
    ),
]

# Property [Timeseries Incompatibilities]: timeseries is incompatible with
# capped, validator, validationLevel, validationAction, and idIndex.
CREATE_TIMESERIES_INCOMPATIBILITY_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="timeseries_incompatible_capped",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "capped": True,
            "size": 4096,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Timeseries incompatible with capped should fail",
    ),
    CommandTestCase(
        id="timeseries_incompatible_validator",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "validator": {"x": {"$exists": True}},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Timeseries incompatible with validator should fail",
    ),
    CommandTestCase(
        id="timeseries_incompatible_validation_level",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "validationLevel": "strict",
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Timeseries incompatible with validationLevel should fail",
    ),
    CommandTestCase(
        id="timeseries_incompatible_validation_action",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "validationAction": "error",
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Timeseries incompatible with validationAction should fail",
    ),
    CommandTestCase(
        id="timeseries_incompatible_id_index",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "idIndex": {"key": {"_id": 1}, "name": "_id_"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Timeseries incompatible with idIndex should fail",
    ),
]

CREATE_TIMESERIES_ERROR_TESTS: list[CommandTestCase] = (
    CREATE_TIMESERIES_TYPE_ERROR_TESTS
    + CREATE_TIMESERIES_TIMEFIELD_ERROR_TESTS
    + CREATE_TIMESERIES_METAFIELD_TYPE_ERROR_TESTS
    + CREATE_TIMESERIES_METAFIELD_ERROR_TESTS
    + CREATE_TIMESERIES_GRANULARITY_ERROR_TESTS
    + CREATE_TIMESERIES_BUCKET_TYPE_ERROR_TESTS
    + CREATE_TIMESERIES_BUCKET_ERROR_TESTS
    + CREATE_TIMESERIES_UNKNOWN_FIELD_ERROR_TESTS
    + CREATE_TIMESERIES_INCOMPATIBILITY_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(CREATE_TIMESERIES_ERROR_TESTS))
def test_create_timeseries_validation(database_client, collection, test):
    """Test create command timeseries validation behavior."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
