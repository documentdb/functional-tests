"""Tests for collMod time series granularity."""

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
)

# Property [Granularity Enum Acceptance]: a granularity equal to one of the
# valid enum strings ("seconds", "minutes", "hours") is accepted, and a null
# granularity is an accepted no-op.
COLLMOD_TS_GRANULARITY_ENUM_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"enum_{gid}",
        target_collection=TimeseriesCollection(),
        docs=[],
        command=lambda ctx, v=val: {"collMod": ctx.collection, "timeseries": {"granularity": v}},
        expected={"ok": Eq(1.0)},
        msg=f"collMod should accept a {gid} granularity",
    )
    for gid, val in [
        ("seconds", "seconds"),
        ("minutes", "minutes"),
        ("hours", "hours"),
        ("null", None),
    ]
]

# Property [Granularity Increase Transition]: a granularity change that
# increases or holds the granularity from a non-default starting granularity is
# accepted, starting from a collection already created at the prior granularity.
COLLMOD_TS_GRANULARITY_TRANSITION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "transition_minutes_to_hours",
        target_collection=TimeseriesCollection(
            timeseries_options={"timeField": "ts", "metaField": "meta", "granularity": "minutes"}
        ),
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "timeseries": {"granularity": "hours"},
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a granularity increase from minutes to hours",
    ),
    CommandTestCase(
        "transition_hours_same_value",
        target_collection=TimeseriesCollection(
            timeseries_options={"timeField": "ts", "metaField": "meta", "granularity": "hours"}
        ),
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "timeseries": {"granularity": "hours"},
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a same-value hours granularity as a no-op",
    ),
]

# Property [Granularity Type Rejection]: a non-string granularity value is
# rejected with a TypeMismatch error.
COLLMOD_TS_GRANULARITY_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"granularity_type_{tid}",
        target_collection=TimeseriesCollection(),
        docs=[],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "timeseries": {"granularity": v},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"collMod should reject a {tid} granularity as the wrong type",
    )
    for tid, val in [
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.0),
        ("decimal", Decimal128("1")),
        ("bool_true", True),
        ("bool_false", False),
        ("array", ["seconds"]),
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

# Property [Granularity Enum Rejection]: the granularity enum is case-sensitive
# and accepts only the exact lowercase seconds, minutes, or hours, so any other
# string (case variants, near-misses, the empty string, and an oversized
# invalid string) produces a BadValue error rather than a string-size error.
COLLMOD_TS_GRANULARITY_ENUM_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"granularity_enum_{tid}",
        target_collection=TimeseriesCollection(),
        docs=[],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "timeseries": {"granularity": v},
        },
        error_code=BAD_VALUE_ERROR,
        msg=f"collMod should reject {tid} as a granularity enum value",
    )
    for tid, val in [
        ("empty", ""),
        ("capitalized", "Seconds"),
        ("uppercase", "SECONDS"),
        ("singular", "second"),
        ("arbitrary", "days"),
        ("large_invalid", "x" * 16_000_000),
    ]
]

# Property [Granularity Decrease Rejection]: a granularity change that decreases
# the granularity is rejected as an invalid transition, starting from a
# collection already created at a higher granularity.
COLLMOD_TS_GRANULARITY_DECREASE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "granularity_decrease_hours_to_minutes",
        target_collection=TimeseriesCollection(
            timeseries_options={"timeField": "ts", "metaField": "meta", "granularity": "hours"}
        ),
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "timeseries": {"granularity": "minutes"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject a granularity decrease from hours to minutes",
    ),
]

COLLMOD_TS_GRANULARITY_TESTS: list[CommandTestCase] = (
    COLLMOD_TS_GRANULARITY_ENUM_TESTS
    + COLLMOD_TS_GRANULARITY_TRANSITION_TESTS
    + COLLMOD_TS_GRANULARITY_TYPE_ERROR_TESTS
    + COLLMOD_TS_GRANULARITY_ENUM_ERROR_TESTS
    + COLLMOD_TS_GRANULARITY_DECREASE_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COLLMOD_TS_GRANULARITY_TESTS))
def test_collMod_time_series_granularity(database_client, collection, test):
    """Test collMod time series granularity acceptance and rejection."""
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
