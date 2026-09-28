"""Tests for collMod top-level expireAfterSeconds on time series collections."""

from __future__ import annotations

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
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.target_collection import (
    ClusteredCollection,
    TimeseriesTTLCollection,
    ViewCollection,
)
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_HALF,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# The time series TTL ceiling is the current epoch seconds: a value at or below
# now is accepted, a value above it is rejected. The tests offset from now by
# this margin in each direction so they do not assume the test runner and server
# clocks match to the second. It is generous enough to absorb realistic clock
# skew plus command latency, while still bracketing the ceiling close enough to
# now that a fixed-constant ceiling could not stay inside the window across runs.
_EPOCH_MARGIN_SECONDS = 60

# Property [Clear TTL]: the exact lowercase string "off" clears the TTL and is
# accepted on both time series and clustered collections.
COLLMOD_TS_EXPIRE_OFF_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "off_timeseries",
        target_collection=TimeseriesTTLCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "expireAfterSeconds": "off"},
        expected={"ok": Eq(1.0)},
        msg="collMod should clear the TTL with 'off' on a time series collection",
    ),
    CommandTestCase(
        "off_clustered",
        target_collection=ClusteredCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "expireAfterSeconds": "off"},
        expected={"ok": Eq(1.0)},
        msg="collMod should clear the TTL with 'off' on a clustered collection",
    ),
]

# Property [Numeric Type Acceptance]: any numeric type is accepted despite the
# declared [string, long] type, with the value set as the TTL on both time
# series and clustered collections.
COLLMOD_TS_EXPIRE_NUMERIC_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "numeric_int32_timeseries",
        target_collection=TimeseriesTTLCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "expireAfterSeconds": 100},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept an int32 expireAfterSeconds on a time series collection",
    ),
    CommandTestCase(
        "numeric_int64_timeseries",
        target_collection=TimeseriesTTLCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "expireAfterSeconds": Int64(100)},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept an int64 expireAfterSeconds on a time series collection",
    ),
    CommandTestCase(
        "numeric_double_timeseries",
        target_collection=TimeseriesTTLCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "expireAfterSeconds": 100.0},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a double expireAfterSeconds on a time series collection",
    ),
    CommandTestCase(
        "numeric_decimal_timeseries",
        target_collection=TimeseriesTTLCollection(),
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "expireAfterSeconds": Decimal128("100"),
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a decimal128 expireAfterSeconds on a time series collection",
    ),
    CommandTestCase(
        "numeric_int32_clustered",
        target_collection=ClusteredCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "expireAfterSeconds": 100},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept an int32 expireAfterSeconds on a clustered collection",
    ),
]

# Property [Positive Fractional Acceptance]: a positive fractional value is
# accepted (the command response does not echo the coerced/stored value).
COLLMOD_TS_EXPIRE_POSITIVE_FRACTIONAL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "positive_fractional_double",
        target_collection=TimeseriesTTLCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "expireAfterSeconds": 100.9},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a positive fractional expireAfterSeconds",
    ),
    CommandTestCase(
        "positive_fractional_decimal",
        target_collection=TimeseriesTTLCollection(),
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "expireAfterSeconds": Decimal128("100.9"),
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a positive fractional decimal128 expireAfterSeconds",
    ),
]

# Property [Negative-to-Zero Acceptance]: a negative value that truncates to 0
# is accepted, exercising the near-boundary partner to the error property where
# a value truncating to <= -1 is rejected.
COLLMOD_TS_EXPIRE_NEGATIVE_ZERO_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "negative_double_near_one",
        target_collection=TimeseriesTTLCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "expireAfterSeconds": -0.9},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a negative double expireAfterSeconds just above -1 as 0",
    ),
    CommandTestCase(
        "negative_decimal",
        target_collection=TimeseriesTTLCollection(),
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "expireAfterSeconds": DECIMAL128_NEGATIVE_HALF,
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a negative decimal expireAfterSeconds as 0",
    ),
]

# Property [NaN Coercion]: a NaN value (float or decimal) is coerced to 0 and
# accepted rather than rejected.
COLLMOD_TS_EXPIRE_NAN_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "nan_float",
        target_collection=TimeseriesTTLCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "expireAfterSeconds": FLOAT_NAN},
        expected={"ok": Eq(1.0)},
        msg="collMod should coerce a float NaN expireAfterSeconds to 0",
    ),
    CommandTestCase(
        "nan_decimal",
        target_collection=TimeseriesTTLCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "expireAfterSeconds": DECIMAL128_NAN},
        expected={"ok": Eq(1.0)},
        msg="collMod should coerce a decimal NaN expireAfterSeconds to 0",
    ),
]

# Property [Epoch Acceptance on Time Series]: a value just below the current
# wall-clock epoch seconds is accepted on a time series collection (the accepted
# partner to the rejection of values above now).
COLLMOD_TS_EXPIRE_EPOCH_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "epoch_just_below_now",
        target_collection=TimeseriesTTLCollection(),
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "expireAfterSeconds": int(time.time()) - _EPOCH_MARGIN_SECONDS,
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should accept an expireAfterSeconds just below the current epoch seconds "
        "on a time series collection",
    ),
]

# Property [Type Rejection]: a top-level expireAfterSeconds value whose type is
# outside the accepted string and numeric types produces a TypeMismatch error.
COLLMOD_TS_EXPIRE_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"expire_type_{tid}",
        target_collection=TimeseriesTTLCollection(),
        docs=[],
        command=lambda ctx, v=val: {"collMod": ctx.collection, "expireAfterSeconds": v},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"collMod should reject a {tid} expireAfterSeconds as the wrong type",
    )
    for tid, val in [
        ("null", None),
        ("bool_true", True),
        ("bool_false", False),
        ("array", [100]),
        ("object", {"a": 1}),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Invalid String Rejection]: any string other than the exact lowercase
# "off" is rejected, including case variants and whitespace-padded forms.
COLLMOD_TS_EXPIRE_STRING_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"string_{sid}",
        target_collection=TimeseriesTTLCollection(),
        docs=[],
        command=lambda ctx, v=val: {"collMod": ctx.collection, "expireAfterSeconds": v},
        error_code=INVALID_OPTIONS_ERROR,
        msg=f"collMod should reject the {sid} string expireAfterSeconds",
    )
    for sid, val in [
        ("title_case", "Off"),
        ("upper_case", "OFF"),
        ("empty", ""),
        ("on", "on"),
        ("trailing_space", "off "),
        ("leading_space", " off"),
    ]
]

# Property [Below-Zero Rejection]: a numeric value that truncates to <= -1 is
# rejected ("cannot be less than 0"), including -Infinity which is rejected as
# below zero rather than as an overflow.
COLLMOD_TS_EXPIRE_BELOW_ZERO_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"below_zero_{nid}",
        target_collection=TimeseriesTTLCollection(),
        docs=[],
        command=lambda ctx, v=val: {"collMod": ctx.collection, "expireAfterSeconds": v},
        error_code=INVALID_OPTIONS_ERROR,
        msg=f"collMod should reject a {nid} expireAfterSeconds as below zero",
    )
    for nid, val in [
        ("int", -1),
        ("double", -1.0),
        ("decimal", Decimal128("-1")),
        ("float_negative_infinity", FLOAT_NEGATIVE_INFINITY),
    ]
]

# Property [Overflow Rejection]: a value that overflows the int64 milliseconds
# conversion is rejected as out of int64 range.
COLLMOD_TS_EXPIRE_OVERFLOW_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"overflow_{oid}",
        target_collection=TimeseriesTTLCollection(),
        docs=[],
        command=lambda ctx, v=val: {"collMod": ctx.collection, "expireAfterSeconds": v},
        error_code=INVALID_OPTIONS_ERROR,
        msg=f"collMod should reject a {oid} expireAfterSeconds as out of int64 range",
    )
    for oid, val in [
        ("float_infinity", FLOAT_INFINITY),
        ("decimal_infinity", DECIMAL128_INFINITY),
        # The smallest int64 whose conversion to milliseconds (the engine's
        # `* 1000` cast) overflows int64, exercising the overflow rejection
        # path distinct from the simpler out-of-range checks.
        ("int64_millis", Int64(9223372036854776)),
    ]
]

# Property [Epoch Ceiling on Time Series]: on a time series collection, a value
# above the current wall-clock epoch seconds is rejected (the rejected partner
# to the acceptance of values below now).
COLLMOD_TS_EXPIRE_EPOCH_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "epoch_above_now",
        target_collection=TimeseriesTTLCollection(),
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "expireAfterSeconds": int(time.time()) + _EPOCH_MARGIN_SECONDS,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject an expireAfterSeconds above the current epoch seconds on a "
        "time series collection",
    ),
]

# Property [Unsupported Target Rejection]: a top-level expireAfterSeconds applied
# to a regular collection or a view is rejected because the option is only
# supported on collections clustered by _id.
COLLMOD_TS_EXPIRE_TARGET_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "expire_target_regular",
        docs=[{"_id": 1}],
        command=lambda ctx: {"collMod": ctx.collection, "expireAfterSeconds": 100},
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject a top-level expireAfterSeconds on a regular collection",
    ),
    CommandTestCase(
        "expire_target_view",
        target_collection=ViewCollection(options={"pipeline": []}),
        docs=[{"_id": 1}],
        command=lambda ctx: {"collMod": ctx.collection, "expireAfterSeconds": 100},
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject a top-level expireAfterSeconds on a view",
    ),
]

COLLMOD_TS_EXPIRE_TESTS: list[CommandTestCase] = (
    COLLMOD_TS_EXPIRE_OFF_TESTS
    + COLLMOD_TS_EXPIRE_NUMERIC_TESTS
    + COLLMOD_TS_EXPIRE_POSITIVE_FRACTIONAL_TESTS
    + COLLMOD_TS_EXPIRE_NEGATIVE_ZERO_TESTS
    + COLLMOD_TS_EXPIRE_NAN_TESTS
    + COLLMOD_TS_EXPIRE_EPOCH_TESTS
    + COLLMOD_TS_EXPIRE_TYPE_ERROR_TESTS
    + COLLMOD_TS_EXPIRE_STRING_ERROR_TESTS
    + COLLMOD_TS_EXPIRE_BELOW_ZERO_ERROR_TESTS
    + COLLMOD_TS_EXPIRE_OVERFLOW_ERROR_TESTS
    + COLLMOD_TS_EXPIRE_EPOCH_ERROR_TESTS
    + COLLMOD_TS_EXPIRE_TARGET_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COLLMOD_TS_EXPIRE_TESTS))
def test_collMod_time_series_expire(database_client, collection, test):
    """Test collMod top-level expireAfterSeconds acceptance and rejection on time series."""
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
