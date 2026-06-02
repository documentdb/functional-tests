"""Tests for killCursors readConcern field."""

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

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    ILLEGAL_OPERATION_ERROR,
    INVALID_OPTIONS_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [readConcern Acceptance]: readConcern with level "local", null,
# empty document, or null level is accepted without error.
KILLCURSORS_READCONCERN_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "readconcern_local",
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": [Int64(1)],
            "readConcern": {"level": "local"},
        },
        expected={
            "cursorsKilled": [],
            "cursorsNotFound": [Int64(1)],
            "cursorsAlive": [],
            "cursorsUnknown": [],
            "ok": 1.0,
        },
        msg="killCursors should accept readConcern with level local",
    ),
    CommandTestCase(
        "readconcern_null",
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": [Int64(1)],
            "readConcern": None,
        },
        expected={
            "cursorsKilled": [],
            "cursorsNotFound": [Int64(1)],
            "cursorsAlive": [],
            "cursorsUnknown": [],
            "ok": 1.0,
        },
        msg="killCursors should accept null readConcern",
    ),
    CommandTestCase(
        "readconcern_empty_doc",
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": [Int64(1)],
            "readConcern": {},
        },
        expected={
            "cursorsKilled": [],
            "cursorsNotFound": [Int64(1)],
            "cursorsAlive": [],
            "cursorsUnknown": [],
            "ok": 1.0,
        },
        msg="killCursors should accept empty readConcern document",
    ),
    CommandTestCase(
        "readconcern_level_null",
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": [Int64(1)],
            "readConcern": {"level": None},
        },
        expected={
            "cursorsKilled": [],
            "cursorsNotFound": [Int64(1)],
            "cursorsAlive": [],
            "cursorsUnknown": [],
            "ok": 1.0,
        },
        msg="killCursors should accept readConcern with null level",
    ),
]

# Property [readConcern Level Rejection]: readConcern with levels other
# than "local" is rejected.
KILLCURSORS_READCONCERN_LEVEL_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "readconcern_majority",
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": [Int64(1)],
            "readConcern": {"level": "majority"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="killCursors should reject readConcern level majority",
    ),
    CommandTestCase(
        "readconcern_available",
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": [Int64(1)],
            "readConcern": {"level": "available"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="killCursors should reject readConcern level available",
    ),
    CommandTestCase(
        "readconcern_linearizable",
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": [Int64(1)],
            "readConcern": {"level": "linearizable"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="killCursors should reject readConcern level linearizable",
    ),
    CommandTestCase(
        "readconcern_snapshot",
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": [Int64(1)],
            "readConcern": {"level": "snapshot"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="killCursors should reject readConcern level snapshot",
    ),
    CommandTestCase(
        "readconcern_level_invalid_name",
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": [Int64(1)],
            "readConcern": {"level": "invalid"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="killCursors should reject unrecognized readConcern level name",
    ),
    CommandTestCase(
        "readconcern_level_wrong_case",
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": [Int64(1)],
            "readConcern": {"level": "Local"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="killCursors should reject wrong-case readConcern level",
    ),
]

# Property [readConcern Type Rejection]: all non-document, non-null BSON
# types for the readConcern field are rejected.
KILLCURSORS_READCONCERN_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"readconcern_type_{tid}",
        command=lambda ctx, v=val: {
            "killCursors": ctx.collection,
            "cursors": [Int64(1)],
            "readConcern": v,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"killCursors should reject {tid} readConcern",
    )
    for tid, val in [
        ("string", "local"),
        ("int32", 42),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("bool", True),
        ("array", [1, 2]),
        ("binary", Binary(b"data")),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("regex", Regex(".*")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [readConcern Subfield Rejection]: invalid subfields, unknown
# fields, and wrong types within the readConcern document are rejected.
KILLCURSORS_READCONCERN_SUBFIELD_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "readconcern_unknown_subfield",
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": [Int64(1)],
            "readConcern": {"bogusField": 1},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="killCursors should reject unknown subfield in readConcern",
    ),
    CommandTestCase(
        "readconcern_unknown_subfield_case_sensitive",
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": [Int64(1)],
            "readConcern": {"Level": "local"},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="killCursors should reject case-mismatched field names in readConcern",
    ),
    CommandTestCase(
        "readconcern_level_empty_string",
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": [Int64(1)],
            "readConcern": {"level": ""},
        },
        error_code=BAD_VALUE_ERROR,
        msg="killCursors should reject empty string readConcern level",
    ),
    CommandTestCase(
        "readconcern_afterclustertime_valid_timestamp",
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": [Int64(1)],
            "readConcern": {"afterClusterTime": Timestamp(1, 1)},
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="killCursors should reject afterClusterTime in readConcern",
    ),
    CommandTestCase(
        "readconcern_provenance_invalid",
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": [Int64(1)],
            "readConcern": {"provenance": "invalid"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="killCursors should reject invalid provenance value",
    ),
]

# Property [readConcern Level Type Rejection]: all non-string, non-null
# types for the readConcern level field are rejected.
KILLCURSORS_READCONCERN_LEVEL_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"readconcern_level_type_{tid}",
        command=lambda ctx, v=val: {
            "killCursors": ctx.collection,
            "cursors": [Int64(1)],
            "readConcern": {"level": v},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"killCursors should reject {tid} type for readConcern level",
    )
    for tid, val in [
        ("int32", 42),
        ("int64", Int64(1)),
        ("double", 1.0),
        ("decimal128", Decimal128("1")),
        ("bool", True),
        ("array", ["local"]),
        ("document", {"a": 1}),
        ("binary", Binary(b"local")),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("regex", Regex("local")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [readConcern afterClusterTime Type Rejection]: all
# non-Timestamp types for afterClusterTime are rejected.
KILLCURSORS_READCONCERN_AFTERCLUSTERTIME_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"readconcern_afterclustertime_type_{tid}",
        command=lambda ctx, v=val: {
            "killCursors": ctx.collection,
            "cursors": [Int64(1)],
            "readConcern": {"afterClusterTime": v},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"killCursors should reject {tid} type for afterClusterTime",
    )
    for tid, val in [
        ("null", None),
        ("int32", 42),
        ("int64", Int64(1)),
        ("double", 1.0),
        ("decimal128", Decimal128("1")),
        ("bool", True),
        ("string", "invalid"),
        ("array", [1, 2]),
        ("document", {"a": 1}),
        ("binary", Binary(b"data")),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("regex", Regex(".*")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [readConcern Provenance Acceptance]: valid provenance values
# and null are accepted.
KILLCURSORS_READCONCERN_PROVENANCE_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"readconcern_provenance_{tid}",
        command=lambda ctx, v=val: {
            "killCursors": ctx.collection,
            "cursors": [Int64(1)],
            "readConcern": {"provenance": v},
        },
        expected={
            "cursorsKilled": [],
            "cursorsNotFound": [Int64(1)],
            "cursorsAlive": [],
            "cursorsUnknown": [],
            "ok": 1.0,
        },
        msg=f"killCursors should accept provenance {tid!r}",
    )
    for tid, val in [
        ("client_supplied", "clientSupplied"),
        ("implicit_default", "implicitDefault"),
        ("custom_default", "customDefault"),
        ("get_last_error_defaults", "getLastErrorDefaults"),
        ("null", None),
    ]
]

KILLCURSORS_READCONCERN_TESTS: list[CommandTestCase] = (
    KILLCURSORS_READCONCERN_ACCEPTANCE_TESTS
    + KILLCURSORS_READCONCERN_LEVEL_ERROR_TESTS
    + KILLCURSORS_READCONCERN_TYPE_ERROR_TESTS
    + KILLCURSORS_READCONCERN_SUBFIELD_ERROR_TESTS
    + KILLCURSORS_READCONCERN_LEVEL_TYPE_ERROR_TESTS
    + KILLCURSORS_READCONCERN_AFTERCLUSTERTIME_TYPE_ERROR_TESTS
    + KILLCURSORS_READCONCERN_PROVENANCE_ACCEPTANCE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(KILLCURSORS_READCONCERN_TESTS))
def test_killCursors_readconcern(collection, test):
    """Test killCursors readConcern field."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
