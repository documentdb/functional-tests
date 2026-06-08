"""Tests for the getMore term field (used by replication)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.cursors.commands.utils.cursor_test_case import (
    CursorCommandContext,
    CursorCommandTestCase,
    open_find_cursors,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [Term Field Accepted]: the "term" field is silently accepted when
# its value is Int64 or null.
GETMORE_TERM_FIELD_ACCEPTED_TESTS: list[CursorCommandTestCase] = [
    CursorCommandTestCase(
        "term_int64",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "term": Int64(1),
        },
        expected={"ok": Eq(1.0)},
        msg="getMore should silently accept 'term' field with Int64 value",
    ),
    CursorCommandTestCase(
        "term_null",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "term": None,
        },
        expected={"ok": Eq(1.0)},
        msg="getMore should silently accept 'term' field with null value",
    ),
]

# Property [Term Field Type Rejection]: all non-Int64, non-null types for the
# term field produce TYPE_MISMATCH_ERROR.
GETMORE_TERM_FIELD_TYPE_ERROR_TESTS: list[CursorCommandTestCase] = [
    CursorCommandTestCase(
        f"term_type_{tid}",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx, v=val: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "term": v,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"getMore should reject {tid} as term field",
    )
    for tid, val in [
        ("int32", 42),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("bool", True),
        ("string", "hello"),
        ("array", [1, 2]),
        ("object", {"a": 1}),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2023, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02")),
        ("regex", Regex(".*")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

GETMORE_TERM_TESTS = GETMORE_TERM_FIELD_ACCEPTED_TESTS + GETMORE_TERM_FIELD_TYPE_ERROR_TESTS


@pytest.mark.parametrize("test_case", pytest_params(GETMORE_TERM_TESTS))
def test_getMore_term(collection, test_case: CursorCommandTestCase):
    """Test getMore term field acceptance and type rejection."""
    collection.insert_many([{"_id": i, "v": i} for i in range(5)])
    cursors = open_find_cursors(
        collection, test_case.cursor_count, batch_size=test_case.find_batch_size
    )
    ctx = CursorCommandContext.from_collection(collection, cursors=cursors)
    result = execute_command(collection, test_case.build_command(ctx))
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        raw_res=True,
    )
