"""Tests for getMore comment field behavior."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.cursors.commands.utils.cursor_test_case import (
    CursorCommandContext,
    CursorCommandTestCase,
    open_find_cursors,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF

# Property [Comment Type Acceptance]: all BSON types are accepted for comment
# without error and no type validation is performed.
GETMORE_COMMENT_TYPE_ACCEPTANCE_TESTS: list[CursorCommandTestCase] = [
    CursorCommandTestCase(
        f"comment_{tid}",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx, v=val: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "comment": v,
        },
        expected={"ok": Eq(1.0)},
        msg=f"getMore should accept {tid} as comment",
    )
    for tid, val in [
        ("string", "hello"),
        ("int32", 42),
        ("int64", Int64(123)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("null", None),
        ("array", [1, "two", 3.0]),
        ("object", {"key": "value"}),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2023, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex("^test", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Comment Does Not Alter Errors]: comment does not prevent or alter
# errors from other invalid parameters.
GETMORE_COMMENT_ERROR_PASSTHROUGH_TESTS: list[CursorCommandTestCase] = [
    CursorCommandTestCase(
        "comment_with_invalid_batch_size",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "batchSize": -1,
            "comment": "test_comment",
        },
        error_code=BAD_VALUE_ERROR,
        msg="getMore should still produce batchSize error when comment is present",
    ),
]

# Property [Comment Omitted Success]: getMore succeeds when the comment field
# is omitted.
GETMORE_COMMENT_OMITTED_SUCCESS_TESTS: list[CursorCommandTestCase] = [
    CursorCommandTestCase(
        "comment_omitted",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {"getMore": ctx.cursors[0], "collection": ctx.collection},
        expected={"ok": Eq(1.0)},
        msg="getMore should succeed when comment is omitted",
    ),
]

GETMORE_COMMENT_TESTS = (
    GETMORE_COMMENT_TYPE_ACCEPTANCE_TESTS
    + GETMORE_COMMENT_ERROR_PASSTHROUGH_TESTS
    + GETMORE_COMMENT_OMITTED_SUCCESS_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(GETMORE_COMMENT_TESTS))
def test_getMore_comment(collection, test_case: CursorCommandTestCase):
    """Test getMore comment field acceptance and error passthrough."""
    collection.insert_many([{"_id": i} for i in range(5)])
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
