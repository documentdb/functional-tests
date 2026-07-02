"""Tests for the collMod readConcern option."""

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
    BAD_VALUE_ERROR,
    INVALID_OPTIONS_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF

# Property [readConcern Acceptance]: readConcern is accepted when it is an empty
# document, the supported "local" level, null (treated as omitted), or an object
# whose level sub-field is null (treated as absent), without changing the
# command result.
COLLMOD_READ_CONCERN_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "empty_document",
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "readConcern": {}},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept an empty readConcern document",
    ),
    CommandTestCase(
        "level_local",
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "readConcern": {"level": "local"}},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a readConcern level of local",
    ),
    CommandTestCase(
        "null",
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "readConcern": None},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a null readConcern as an omitted field",
    ),
    CommandTestCase(
        "level_null",
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "readConcern": {"level": None}},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a null readConcern level as an absent sub-field",
    ),
]

# Property [readConcern Unsupported Level Rejection]: a recognized read concern
# level that collMod does not support (majority, available, snapshot,
# linearizable) produces an InvalidOptions error.
COLLMOD_READ_CONCERN_UNSUPPORTED_LEVEL_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"unsupported_{level}",
        docs=[],
        command=lambda ctx, v=level: {"collMod": ctx.collection, "readConcern": {"level": v}},
        error_code=INVALID_OPTIONS_ERROR,
        msg=f"collMod should reject the {level} readConcern level as unsupported",
    )
    for level in ["majority", "available", "snapshot", "linearizable"]
]

# Property [readConcern Invalid Level Enum Rejection]: the level enum is
# case-sensitive and applies no whitespace trimming, so any string that is not a
# recognized level produces a BadValue error.
COLLMOD_READ_CONCERN_INVALID_LEVEL_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"invalid_level_{tid}",
        docs=[],
        command=lambda ctx, v=val: {"collMod": ctx.collection, "readConcern": {"level": v}},
        error_code=BAD_VALUE_ERROR,
        msg=f"collMod should reject {tid} as a readConcern level enum value",
    )
    for tid, val in [
        ("empty", ""),
        ("arbitrary", "bogus"),
        ("capitalized", "Local"),
        ("uppercase", "LOCAL"),
        ("trailing_space", "local "),
    ]
]

# Property [readConcern.level Type Rejection]: a level sub-field value that is
# neither a string nor null produces a TypeMismatch error.
COLLMOD_READ_CONCERN_LEVEL_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"level_type_{tid}",
        docs=[],
        command=lambda ctx, v=val: {"collMod": ctx.collection, "readConcern": {"level": v}},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"collMod should reject a {tid} readConcern level as a non-string",
    )
    for tid, val in [
        ("int32", 42),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool_true", True),
        ("bool_false", False),
        ("array", ["local"]),
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

# Property [readConcern Top-Level Type Rejection]: a readConcern value that is
# neither an object nor null produces a TypeMismatch error.
COLLMOD_READ_CONCERN_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"type_{tid}",
        docs=[],
        command=lambda ctx, v=val: {"collMod": ctx.collection, "readConcern": v},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"collMod should reject a {tid} readConcern as a non-object",
    )
    for tid, val in [
        ("string", "local"),
        ("int32", 42),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool_true", True),
        ("bool_false", False),
        ("array", [{"level": "local"}]),
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

# Property [readConcern Unknown Sub-Field Rejection]: an unrecognized
# readConcern sub-field produces an UnknownField error, and that error fires
# even when the supported level sub-field is also present.
COLLMOD_READ_CONCERN_UNKNOWN_FIELD_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unknown_field_only",
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "readConcern": {"bogus": 1}},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="collMod should reject an unknown readConcern sub-field",
    ),
    CommandTestCase(
        "unknown_field_with_level",
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "readConcern": {"level": "local", "bogus": 1},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="collMod should reject an unknown readConcern sub-field even with a level present",
    ),
]

COLLMOD_READ_CONCERN_ALL_TESTS: list[CommandTestCase] = (
    COLLMOD_READ_CONCERN_SUCCESS_TESTS
    + COLLMOD_READ_CONCERN_UNSUPPORTED_LEVEL_ERROR_TESTS
    + COLLMOD_READ_CONCERN_INVALID_LEVEL_ERROR_TESTS
    + COLLMOD_READ_CONCERN_LEVEL_TYPE_ERROR_TESTS
    + COLLMOD_READ_CONCERN_TYPE_ERROR_TESTS
    + COLLMOD_READ_CONCERN_UNKNOWN_FIELD_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COLLMOD_READ_CONCERN_ALL_TESTS))
def test_collMod_read_concern(database_client, collection, test):
    """Test collMod readConcern option behavior."""
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
