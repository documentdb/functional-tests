"""Tests for the collMod changeStreamPreAndPostImages option."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    INVALID_OPTIONS_ERROR,
    MISSING_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.target_collection import (
    TimeseriesCollection,
    ViewCollection,
)
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF

# Property [changeStreamPreAndPostImages Success]: a null value is accepted as
# an omitted field, and an object with a boolean enabled sub-field is accepted
# for either truth value on a regular collection.
COLLMOD_CHANGE_STREAM_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "null",
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "changeStreamPreAndPostImages": None,
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a null changeStreamPreAndPostImages as an omitted field",
    ),
    CommandTestCase(
        "enabled_true",
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "changeStreamPreAndPostImages": {"enabled": True},
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should accept changeStreamPreAndPostImages with enabled true",
    ),
    CommandTestCase(
        "enabled_false",
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "changeStreamPreAndPostImages": {"enabled": False},
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should accept changeStreamPreAndPostImages with enabled false",
    ),
]

# Property [changeStreamPreAndPostImages Top-Level Type Rejection]: a
# changeStreamPreAndPostImages value that is neither an object nor null produces
# a TypeMismatch error.
COLLMOD_CHANGE_STREAM_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"toplevel_type_{tid}",
        docs=[],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "changeStreamPreAndPostImages": v,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"collMod should reject a {tid} changeStreamPreAndPostImages as a non-object",
    )
    for tid, val in [
        ("string", "x"),
        ("int32", 42),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool_true", True),
        ("bool_false", False),
        ("array", [{"enabled": True}]),
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

# Property [changeStreamPreAndPostImages Missing enabled]: a
# changeStreamPreAndPostImages object whose enabled sub-field is absent or null
# produces a FailedToParse error because enabled is required and a null value is
# treated as missing rather than as a type mismatch.
COLLMOD_CHANGE_STREAM_MISSING_ENABLED_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "missing_enabled",
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "changeStreamPreAndPostImages": {},
        },
        error_code=MISSING_FIELD_ERROR,
        msg="collMod should reject changeStreamPreAndPostImages with no enabled sub-field",
    ),
    CommandTestCase(
        "enabled_null",
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "changeStreamPreAndPostImages": {"enabled": None},
        },
        error_code=MISSING_FIELD_ERROR,
        msg="collMod should treat a null enabled as a missing required sub-field",
    ),
]

# Property [changeStreamPreAndPostImages Unknown Sub-Field]: a
# changeStreamPreAndPostImages object containing an unrecognized sub-field
# produces an UnknownField error, and that error fires even when the required
# enabled sub-field is also present.
COLLMOD_CHANGE_STREAM_UNKNOWN_FIELD_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unknown_field_only",
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "changeStreamPreAndPostImages": {"bogus": 1},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="collMod should reject an unknown changeStreamPreAndPostImages sub-field",
    ),
    CommandTestCase(
        "unknown_field_with_enabled",
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "changeStreamPreAndPostImages": {"bogus": 1, "enabled": True},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="collMod should reject an unknown sub-field before the missing-enabled check",
    ),
]

# Property [changeStreamPreAndPostImages enabled Type Rejection]: an enabled
# sub-field whose value is neither a boolean nor absent produces a TypeMismatch
# error.
COLLMOD_CHANGE_STREAM_ENABLED_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"enabled_type_{tid}",
        docs=[],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "changeStreamPreAndPostImages": {"enabled": v},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"collMod should reject a {tid} enabled value as a non-boolean",
    )
    for tid, val in [
        ("string", "true"),
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.0),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("array", [True]),
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

# Property [changeStreamPreAndPostImages Unsupported Collection Type]: applying
# changeStreamPreAndPostImages to a view or a time series collection produces an
# InvalidOptions error regardless of the enabled truth value.
COLLMOD_CHANGE_STREAM_UNSUPPORTED_TARGET_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"{target_id}_enabled_{enabled_id}",
        docs=[],
        target_collection=target,
        command=lambda ctx, e=enabled: {
            "collMod": ctx.collection,
            "changeStreamPreAndPostImages": {"enabled": e},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg=f"collMod should reject changeStreamPreAndPostImages on a {target_id}",
    )
    for target_id, target in [
        ("view", ViewCollection()),
        ("timeseries", TimeseriesCollection()),
    ]
    for enabled_id, enabled in [("true", True), ("false", False)]
]

COLLMOD_CHANGE_STREAM_ERROR_TESTS: list[CommandTestCase] = (
    COLLMOD_CHANGE_STREAM_TYPE_ERROR_TESTS
    + COLLMOD_CHANGE_STREAM_MISSING_ENABLED_ERROR_TESTS
    + COLLMOD_CHANGE_STREAM_UNKNOWN_FIELD_ERROR_TESTS
    + COLLMOD_CHANGE_STREAM_ENABLED_TYPE_ERROR_TESTS
    + COLLMOD_CHANGE_STREAM_UNSUPPORTED_TARGET_ERROR_TESTS
)

COLLMOD_CHANGE_STREAM_ALL_TESTS: list[CommandTestCase] = (
    COLLMOD_CHANGE_STREAM_SUCCESS_TESTS + COLLMOD_CHANGE_STREAM_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COLLMOD_CHANGE_STREAM_ALL_TESTS))
def test_collMod_change_streams(database_client, collection, test):
    """Test collMod changeStreamPreAndPostImages option behavior."""
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
