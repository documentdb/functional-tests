"""Tests for planCacheClear command comment field type acceptance."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Comment Type Acceptance]: comment field accepts any valid BSON type.
COMMENT_TYPE_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"comment_type_{tid}",
        command=lambda ctx, v=val: {"planCacheClear": ctx.collection, "comment": v},
        expected={"ok": 1.0},
        msg=f"planCacheClear should accept {tid} as comment field",
    )
    for tid, val in [
        ("string", "test"),
        ("int", 42),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("decimal128", Decimal128("1")),
        ("bool_true", True),
        ("bool_false", False),
        ("null", None),
        ("array", [1, 2, 3]),
        ("object", {"key": "value"}),
        ("binary", Binary(b"\x00")),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("regex", Regex(".*")),
        ("timestamp", Timestamp(0, 0)),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

COMBINED_LIST: list[CommandTestCase] = COMMENT_TYPE_ACCEPTANCE_TESTS


@pytest.mark.parametrize("test", pytest_params(COMBINED_LIST))
def test_planCacheClear_comment(database_client, collection, test):
    """Test planCacheClear comment field type acceptance."""
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
