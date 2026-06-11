"""Tests for count command comment acceptance."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Comment Acceptance]: all pymongo-representable BSON types are
# accepted for the comment field without error.
COUNT_COMMENT_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"comment_{tid}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {"count": ctx.collection, "comment": v},
        expected={"n": 1, "ok": 1.0},
        msg=f"count should accept {tid} comment",
    )
    for tid, val in [
        ("int32", 42),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("string", "hello"),
        ("bool", True),
        ("null", None),
        ("array", [1, 2, 3]),
        ("object", {"key": "value"}),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02")),
        ("regex", Regex("^abc")),
        ("code", Code("function(){}")),
        ("code_with_scope", Code("function(){}", {"x": 1})),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]


@pytest.mark.parametrize("test", pytest_params(COUNT_COMMENT_ACCEPTANCE_TESTS))
def test_count_comment(database_client, collection, test):
    """Test count command comment acceptance."""
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
