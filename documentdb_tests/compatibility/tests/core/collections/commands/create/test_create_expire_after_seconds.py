"""Tests for the create command expireAfterSeconds parameter."""

import time
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
    INVALID_OPTIONS_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_HALF,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
)

# Property [ExpireAfterSeconds Type Acceptance]: expireAfterSeconds accepts
# int32, Int64, double, and Decimal128 on timeseries or clustered collections;
# null is treated as omitted.
CREATE_EXPIRE_AFTER_SECONDS_TYPE_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="eas_int32_timeseries",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "expireAfterSeconds": 3600,
        },
        expected={"ok": 1.0},
        msg="int32 expireAfterSeconds on timeseries should succeed",
    ),
    CommandTestCase(
        id="eas_int64_timeseries",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "expireAfterSeconds": Int64(3600),
        },
        expected={"ok": 1.0},
        msg="Int64 expireAfterSeconds on timeseries should succeed",
    ),
    CommandTestCase(
        id="eas_double_timeseries",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "expireAfterSeconds": 3600.0,
        },
        expected={"ok": 1.0},
        msg="double expireAfterSeconds on timeseries should succeed",
    ),
    CommandTestCase(
        id="eas_decimal128_timeseries",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "expireAfterSeconds": Decimal128("3600"),
        },
        expected={"ok": 1.0},
        msg="Decimal128 expireAfterSeconds on timeseries should succeed",
    ),
    CommandTestCase(
        id="eas_null_treated_as_omitted",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "expireAfterSeconds": None,
        },
        expected={"ok": 1.0},
        msg="null expireAfterSeconds is treated as omitted",
    ),
    CommandTestCase(
        id="eas_clustered_collection",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}, "unique": True},
            "expireAfterSeconds": 3600,
        },
        expected={"ok": 1.0},
        msg="expireAfterSeconds on clustered collection should succeed",
    ),
    CommandTestCase(
        id="eas_zero",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "expireAfterSeconds": 0,
        },
        expected={"ok": 1.0},
        msg="expireAfterSeconds=0 should succeed",
    ),
]

# Property [ExpireAfterSeconds Coercion]: doubles truncate toward zero;
# Decimal128 uses banker's rounding; NaN and -0.0 are stored as 0; negative
# fractional values that coerce to 0 succeed.
CREATE_EXPIRE_AFTER_SECONDS_COERCION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="eas_double_truncation",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "expireAfterSeconds": 100.9,
        },
        expected={"ok": 1.0},
        msg="double 100.9 truncates toward zero to 100",
    ),
    CommandTestCase(
        id="eas_decimal128_bankers_rounding",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "expireAfterSeconds": Decimal128("100.5"),
        },
        expected={"ok": 1.0},
        msg="Decimal128('100.5') banker's rounds to 100",
    ),
    CommandTestCase(
        id="eas_nan_stored_as_zero",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "expireAfterSeconds": FLOAT_NAN,
        },
        expected={"ok": 1.0},
        msg="NaN is stored as 0",
    ),
    CommandTestCase(
        id="eas_negative_nan_stored_as_zero",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "expireAfterSeconds": FLOAT_NEGATIVE_NAN,
        },
        expected={"ok": 1.0},
        msg="-NaN is stored as 0",
    ),
    CommandTestCase(
        id="eas_decimal128_nan_stored_as_zero",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "expireAfterSeconds": DECIMAL128_NAN,
        },
        expected={"ok": 1.0},
        msg="Decimal128 NaN is stored as 0",
    ),
    CommandTestCase(
        id="eas_decimal128_negative_nan_stored_as_zero",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "expireAfterSeconds": DECIMAL128_NEGATIVE_NAN,
        },
        expected={"ok": 1.0},
        msg="Decimal128 -NaN is stored as 0",
    ),
    CommandTestCase(
        id="eas_negative_zero_double",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "expireAfterSeconds": DOUBLE_NEGATIVE_ZERO,
        },
        expected={"ok": 1.0},
        msg="-0.0 is stored as 0",
    ),
    CommandTestCase(
        id="eas_decimal128_negative_zero",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "expireAfterSeconds": DECIMAL128_NEGATIVE_ZERO,
        },
        expected={"ok": 1.0},
        msg="Decimal128('-0') is stored as 0",
    ),
    CommandTestCase(
        id="eas_double_neg_0_9_truncates_to_zero",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "expireAfterSeconds": -0.9,
        },
        expected={"ok": 1.0},
        msg="double -0.9 truncates toward zero to 0, which succeeds",
    ),
    CommandTestCase(
        id="eas_decimal128_neg_0_5_rounds_to_zero",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "expireAfterSeconds": DECIMAL128_NEGATIVE_HALF,
        },
        expected={"ok": 1.0},
        msg="Decimal128('-0.5') banker's rounds to 0, which succeeds",
    ),
    CommandTestCase(
        id="eas_upper_bound_current_epoch",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "expireAfterSeconds": int(time.time()),
        },
        expected={"ok": 1.0},
        msg="Value at current epoch seconds (upper bound) should succeed",
    ),
]

# Property [ExpireAfterSeconds Type Strictness]: non-numeric types (including
# bool) for expireAfterSeconds produce TYPE_MISMATCH_ERROR.
CREATE_EXPIRE_AFTER_SECONDS_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id=f"eas_err_{tid}",
        command=lambda ctx, v=val, t=tid: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "expireAfterSeconds": v,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"{tid} for expireAfterSeconds should fail",
    )
    for tid, val in [
        ("bool_true", True),
        ("bool_false", False),
        ("string", "3600"),
        ("object", {"a": 1}),
        ("array", [3600]),
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

# Property [ExpireAfterSeconds Collection Type Restriction]: expireAfterSeconds
# on regular, capped, or view collections produces INVALID_OPTIONS_ERROR.
CREATE_EXPIRE_AFTER_SECONDS_COLLECTION_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="eas_err_regular_collection",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "expireAfterSeconds": 3600,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="expireAfterSeconds on regular collection should fail",
    ),
    CommandTestCase(
        id="eas_err_capped_collection",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 4096,
            "expireAfterSeconds": 3600,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="expireAfterSeconds on capped collection should fail",
    ),
    CommandTestCase(
        id="eas_err_view",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": "other",
            "pipeline": [],
            "expireAfterSeconds": 3600,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="viewOn + expireAfterSeconds should fail",
    ),
]

# Property [ExpireAfterSeconds Value Rejection]: negative values after coercion,
# overflow (value * 1000 > INT64_MAX), values exceeding current epoch, and
# Infinity all produce INVALID_OPTIONS_ERROR.
CREATE_EXPIRE_AFTER_SECONDS_VALUE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="eas_err_negative_int",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "expireAfterSeconds": -1,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Negative int expireAfterSeconds should fail",
    ),
    CommandTestCase(
        id="eas_err_negative_infinity",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "expireAfterSeconds": FLOAT_NEGATIVE_INFINITY,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="-Infinity coerces to negative, should fail",
    ),
    CommandTestCase(
        id="eas_err_decimal128_negative_infinity",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "expireAfterSeconds": DECIMAL128_NEGATIVE_INFINITY,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Decimal128 -Infinity coerces to negative, should fail",
    ),
    CommandTestCase(
        id="eas_err_decimal128_neg_0_9_rounds_to_neg_1",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "expireAfterSeconds": Decimal128("-0.9"),
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Decimal128('-0.9') banker's rounds to -1, should fail",
    ),
    CommandTestCase(
        id="eas_err_overflow",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "expireAfterSeconds": Int64(9_223_372_036_854_776),
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Overflow (value * 1000 > INT64_MAX) should fail",
    ),
    CommandTestCase(
        id="eas_err_infinity",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "expireAfterSeconds": FLOAT_INFINITY,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Infinity coerces to INT64_MAX, overflow should fail",
    ),
    CommandTestCase(
        id="eas_err_decimal128_infinity",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "expireAfterSeconds": DECIMAL128_INFINITY,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Decimal128 Infinity overflow should fail",
    ),
    CommandTestCase(
        id="eas_err_exceeds_epoch",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "expireAfterSeconds": 9_999_999_999,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Value exceeding current epoch should fail",
    ),
    CommandTestCase(
        id="eas_err_exceeds_epoch_clustered",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}, "unique": True},
            "expireAfterSeconds": 9_999_999_999,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Value exceeding current epoch on clustered collection should fail",
    ),
]

CREATE_EXPIRE_AFTER_SECONDS_TESTS: list[CommandTestCase] = (
    CREATE_EXPIRE_AFTER_SECONDS_TYPE_ACCEPTANCE_TESTS
    + CREATE_EXPIRE_AFTER_SECONDS_COERCION_TESTS
    + CREATE_EXPIRE_AFTER_SECONDS_TYPE_ERROR_TESTS
    + CREATE_EXPIRE_AFTER_SECONDS_COLLECTION_TYPE_ERROR_TESTS
    + CREATE_EXPIRE_AFTER_SECONDS_VALUE_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(CREATE_EXPIRE_AFTER_SECONDS_TESTS))
def test_create_expire_after_seconds(database_client, collection, test):
    """Test create command expire after seconds behavior."""
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
