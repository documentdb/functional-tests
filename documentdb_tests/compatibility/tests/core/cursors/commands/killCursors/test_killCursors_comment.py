"""Tests for killCursors comment field type acceptance."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
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
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF

# Property [comment Field Universal Type Acceptance]: all BSON types
# representable by pymongo are accepted for the comment field without
# restriction.
KILLCURSORS_COMMENT_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"comment_{tid}",
        command=lambda ctx, v=val: {
            "killCursors": ctx.collection,
            "cursors": [Int64(1)],
            "comment": v,
        },
        expected={
            "cursorsKilled": [],
            "cursorsNotFound": [Int64(1)],
            "cursorsAlive": [],
            "cursorsUnknown": [],
            "ok": 1.0,
        },
        msg=f"killCursors should accept {tid} comment",
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
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]


@pytest.mark.parametrize("test", pytest_params(KILLCURSORS_COMMENT_TYPE_TESTS))
def test_killCursors_comment(collection, test):
    """Test killCursors comment field type acceptance."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
