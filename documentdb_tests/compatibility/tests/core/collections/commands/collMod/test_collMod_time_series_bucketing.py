"""Tests for collMod time series bucketing (bucketRoundingSeconds / bucketMaxSpanSeconds)."""

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

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    INVALID_OPTIONS_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.target_collection import (
    TimeseriesCollection,
    TimeseriesCustomBucketCollection,
)
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    FLOAT_INFINITY,
    FLOAT_NAN,
    INT64_MAX,
)

# Property [Bucketing Numeric Type Coercion]: the coupled `bucketRoundingSeconds`
# and `bucketMaxSpanSeconds` accept any numeric type.
COLLMOD_TS_BUCKET_NUMERIC_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "numeric_int32",
        target_collection=TimeseriesCustomBucketCollection(bucket_seconds=100),
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "timeseries": {"bucketRoundingSeconds": 200, "bucketMaxSpanSeconds": 200},
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should accept int32 bucketing seconds",
    ),
    CommandTestCase(
        "numeric_int64",
        target_collection=TimeseriesCustomBucketCollection(bucket_seconds=100),
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "timeseries": {
                "bucketRoundingSeconds": Int64(200),
                "bucketMaxSpanSeconds": Int64(200),
            },
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should accept int64 bucketing seconds",
    ),
    CommandTestCase(
        "numeric_double",
        target_collection=TimeseriesCustomBucketCollection(bucket_seconds=100),
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "timeseries": {"bucketRoundingSeconds": 200.0, "bucketMaxSpanSeconds": 200.0},
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should accept double bucketing seconds",
    ),
    CommandTestCase(
        "numeric_decimal",
        target_collection=TimeseriesCustomBucketCollection(bucket_seconds=100),
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "timeseries": {
                "bucketRoundingSeconds": Decimal128("200"),
                "bucketMaxSpanSeconds": Decimal128("200"),
            },
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should accept decimal128 bucketing seconds",
    ),
]

# Property [Bucketing Equality After Truncation]: the two coupled fields must be
# equal, and equality is checked after truncation toward zero, so distinct
# fractional inputs that truncate to the same integer are accepted as equal.
COLLMOD_TS_BUCKET_EQUALITY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "equal_after_truncation",
        target_collection=TimeseriesCustomBucketCollection(bucket_seconds=100),
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "timeseries": {
                "bucketRoundingSeconds": 200.9,
                "bucketMaxSpanSeconds": 200.1,
            },
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should accept bucketing seconds that are equal only after truncation",
    ),
]

# Property [Bucketing Range Boundaries]: the lower and upper boundary values
# are both accepted (the range is inclusive at both ends).
COLLMOD_TS_BUCKET_BOUNDARY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "lower_boundary_1",
        target_collection=TimeseriesCustomBucketCollection(bucket_seconds=1),
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "timeseries": {"bucketRoundingSeconds": 1, "bucketMaxSpanSeconds": 1},
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should accept the lower boundary bucketing seconds of 1",
    ),
    CommandTestCase(
        "upper_boundary_31536000",
        target_collection=TimeseriesCollection(),
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "timeseries": {
                "bucketRoundingSeconds": 31_536_000,
                "bucketMaxSpanSeconds": 31_536_000,
            },
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should accept the upper boundary bucketing seconds of 31536000",
    ),
]

# Property [Bucketing Increase-Only Inclusive]: a new bucketing value greater
# than or equal to the existing/implied value is accepted, including a new value
# equal to the value implied by the seconds granularity.
COLLMOD_TS_BUCKET_INCREASE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "equal_implied_3600",
        target_collection=TimeseriesCollection(),
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "timeseries": {"bucketRoundingSeconds": 3600, "bucketMaxSpanSeconds": 3600},
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a new bucketing value equal to the implied 3600",
    ),
]

# Property [Bucketing Null No-Op]: a null value for both coupled fields is an
# accepted no-op.
COLLMOD_TS_BUCKET_NULL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "null_both",
        target_collection=TimeseriesCollection(),
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "timeseries": {"bucketRoundingSeconds": None, "bucketMaxSpanSeconds": None},
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should accept null bucketing seconds as a no-op",
    ),
]

# Property [Bucketing Type Rejection]: a non-numeric bucketing value is rejected
# with a TypeMismatch error, and an array is not unwrapped into a numeric value.
COLLMOD_TS_BUCKET_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"bucket_type_{tid}",
        target_collection=TimeseriesCollection(),
        docs=[],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "timeseries": {"bucketRoundingSeconds": v, "bucketMaxSpanSeconds": v},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"collMod should reject a {tid} bucketing value as the wrong type",
    )
    for tid, val in [
        ("string", "x"),
        ("bool_true", True),
        ("bool_false", False),
        ("array", [1]),
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

# Property [Bucketing Below-Minimum Rejection]: a bucketing value below the
# minimum after truncation toward zero is rejected with a BadValue error,
# including values that coerce to zero (a fraction truncates, NaN coerces).
COLLMOD_TS_BUCKET_BELOW_MIN_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"bucket_below_min_{nid}",
        target_collection=TimeseriesCollection(),
        docs=[],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "timeseries": {"bucketRoundingSeconds": v, "bucketMaxSpanSeconds": v},
        },
        error_code=BAD_VALUE_ERROR,
        msg=f"collMod should reject a {nid} bucketing value as below the minimum of 1",
    )
    for nid, val in [
        ("zero", 0),
        ("negative", -1),
        ("half", 0.5),
        ("nan_float", FLOAT_NAN),
        ("nan_decimal", DECIMAL128_NAN),
    ]
]

# Property [Bucketing Above-Maximum Rejection]: a bucketing value above the
# maximum after coercion is rejected with a BadValue error, including infinite and
# int64-max inputs that clamp to int32 max and still exceed the ceiling.
COLLMOD_TS_BUCKET_ABOVE_MAX_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"bucket_above_max_{nid}",
        target_collection=TimeseriesCollection(),
        docs=[],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "timeseries": {"bucketRoundingSeconds": v, "bucketMaxSpanSeconds": v},
        },
        error_code=BAD_VALUE_ERROR,
        msg=f"collMod should reject a {nid} bucketing value as above the maximum of 31536000",
    )
    for nid, val in [
        ("just_above", 31_536_001),
        ("float_infinity", FLOAT_INFINITY),
        ("decimal_infinity", DECIMAL128_INFINITY),
        ("int64_max", INT64_MAX),
    ]
]

# Property [Bucketing Coupling Rejection]: setting only one of the two coupled
# fields, or setting them to values that are unequal after truncation, is
# rejected with an InvalidOptions error.
COLLMOD_TS_BUCKET_COUPLING_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "only_max_span",
        target_collection=TimeseriesCollection(),
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "timeseries": {"bucketMaxSpanSeconds": 3600},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject setting only bucketMaxSpanSeconds without bucketRoundingSeconds",
    ),
    CommandTestCase(
        "only_rounding",
        target_collection=TimeseriesCollection(),
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "timeseries": {"bucketRoundingSeconds": 3600},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject setting only bucketRoundingSeconds without bucketMaxSpanSeconds",
    ),
    CommandTestCase(
        "unequal_after_truncation",
        target_collection=TimeseriesCollection(),
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "timeseries": {
                "bucketRoundingSeconds": 3600.9,
                "bucketMaxSpanSeconds": 3601.1,
            },
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject coupled bucketing values that are unequal after truncation",
    ),
]

# Property [Bucketing Decrease Rejection]: a new bucketing value less than the
# existing/implied bucketMaxSpanSeconds is rejected with an InvalidOptions
# error, with the value implied by the seconds granularity as the threshold.
COLLMOD_TS_BUCKET_DECREASE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "below_implied_3600",
        target_collection=TimeseriesCollection(),
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "timeseries": {"bucketRoundingSeconds": 3599, "bucketMaxSpanSeconds": 3599},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject a new bucketing value below the implied 3600",
    ),
]

# Property [Bucketing With Granularity Rejection]: combining granularity with a
# custom bucketing value that differs from the granularity's default in the same
# timeseries document is rejected with an InvalidOptions error.
COLLMOD_TS_BUCKET_WITH_GRANULARITY_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "granularity_and_both",
        target_collection=TimeseriesCollection(),
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "timeseries": {
                "granularity": "seconds",
                "bucketRoundingSeconds": 7200,
                "bucketMaxSpanSeconds": 7200,
            },
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject granularity combined with non-default bucketing fields",
    ),
]

COLLMOD_TS_BUCKETING_TESTS: list[CommandTestCase] = (
    COLLMOD_TS_BUCKET_NUMERIC_TESTS
    + COLLMOD_TS_BUCKET_EQUALITY_TESTS
    + COLLMOD_TS_BUCKET_BOUNDARY_TESTS
    + COLLMOD_TS_BUCKET_INCREASE_TESTS
    + COLLMOD_TS_BUCKET_NULL_TESTS
    + COLLMOD_TS_BUCKET_TYPE_ERROR_TESTS
    + COLLMOD_TS_BUCKET_BELOW_MIN_ERROR_TESTS
    + COLLMOD_TS_BUCKET_ABOVE_MAX_ERROR_TESTS
    + COLLMOD_TS_BUCKET_COUPLING_ERROR_TESTS
    + COLLMOD_TS_BUCKET_DECREASE_ERROR_TESTS
    + COLLMOD_TS_BUCKET_WITH_GRANULARITY_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COLLMOD_TS_BUCKETING_TESTS))
def test_collMod_time_series_bucketing(database_client, collection, test):
    """Test collMod time series bucketing acceptance and rejection."""
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
