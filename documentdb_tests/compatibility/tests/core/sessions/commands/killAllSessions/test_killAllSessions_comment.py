"""Tests for killAllSessions comment field type acceptance."""

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
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.no_parallel

# Property [Comment Type Acceptance]: the comment field accepts any BSON
# type.
KILLALLSESSIONS_COMMENT_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"comment_{tid}",
        command=lambda ctx, v=val: {"killAllSessions": [], "comment": v},
        expected={"ok": 1.0},
        msg=f"killAllSessions should accept {tid} comment",
    )
    for tid, val in [
        ("string", "test comment"),
        ("string_empty", ""),
        ("int32", 42),
        ("int64", Int64(123)),
        ("double", 3.14),
        ("decimal128", Decimal128("1.5")),
        ("bool_true", True),
        ("bool_false", False),
        ("null", None),
        ("object", {"key": "value"}),
        ("object_empty", {}),
        ("array", [1, "two", 3.0]),
        ("array_empty", []),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("binary", Binary(b"\x00\x01\x02")),
        ("regex", Regex(".*", "i")),
        ("timestamp", Timestamp(1, 1)),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("code", Code("function(){}")),
    ]
]


@pytest.mark.parametrize("test", pytest_params(KILLALLSESSIONS_COMMENT_TYPE_TESTS))
def test_killAllSessions_comment(collection, test):
    """Test killAllSessions comment field type acceptance."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
