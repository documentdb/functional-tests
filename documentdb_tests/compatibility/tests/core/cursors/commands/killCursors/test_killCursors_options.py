"""Tests for killCursors optional fields and command options."""

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
    INVALID_OPTIONS_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Null and Missing Behavior (Success Cases)]: null values for
# optional fields (comment, maxTimeMS) and null elements in the cursors
# array are silently accepted without error.
KILLCURSORS_NULL_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "null_comment_omitted",
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": [Int64(1)],
        },
        expected={
            "cursorsKilled": [],
            "cursorsNotFound": [Int64(1)],
            "cursorsAlive": [],
            "cursorsUnknown": [],
            "ok": 1.0,
        },
        msg="killCursors should accept omitted comment field without error",
    ),
    CommandTestCase(
        "null_max_time_ms",
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": [Int64(1)],
            "maxTimeMS": None,
        },
        expected={
            "cursorsKilled": [],
            "cursorsNotFound": [Int64(1)],
            "cursorsAlive": [],
            "cursorsUnknown": [],
            "ok": 1.0,
        },
        msg="killCursors should accept null maxTimeMS without error",
    ),
]

# Property [Unrecognized Fields]: any unrecognized field in the command
# is rejected.
KILLCURSORS_UNRECOGNIZED_FIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unrecognized_field",
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": [Int64(1)],
            "bogusField": 123,
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="killCursors should reject an unrecognized field",
    ),
]

# Property [writeConcern Rejection]: the command does not support
# writeConcern; a document value is rejected while null is accepted.
KILLCURSORS_WRITECONCERN_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "writeconcern_rejected",
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": [Int64(1)],
            "writeConcern": {},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="killCursors should reject writeConcern",
    ),
    CommandTestCase(
        "writeconcern_null",
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": [Int64(1)],
            "writeConcern": None,
        },
        expected={
            "cursorsKilled": [],
            "cursorsNotFound": [Int64(1)],
            "cursorsAlive": [],
            "cursorsUnknown": [],
            "ok": 1.0,
        },
        msg="killCursors should accept null writeConcern",
    ),
]

# Property [writeConcern Type Rejection]: all non-document, non-null BSON
# types for the writeConcern field are rejected.
KILLCURSORS_WRITECONCERN_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"writeconcern_type_{tid}",
        command=lambda ctx, v=val: {
            "killCursors": ctx.collection,
            "cursors": [Int64(1)],
            "writeConcern": v,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"killCursors should reject {tid} writeConcern",
    )
    for tid, val in [
        ("string", "majority"),
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

KILLCURSORS_OPTIONS_TESTS: list[CommandTestCase] = (
    KILLCURSORS_NULL_SUCCESS_TESTS
    + KILLCURSORS_UNRECOGNIZED_FIELD_TESTS
    + KILLCURSORS_WRITECONCERN_TESTS
    + KILLCURSORS_WRITECONCERN_TYPE_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(KILLCURSORS_OPTIONS_TESTS))
def test_killCursors_options(collection, test):
    """Test killCursors optional fields and command options."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
