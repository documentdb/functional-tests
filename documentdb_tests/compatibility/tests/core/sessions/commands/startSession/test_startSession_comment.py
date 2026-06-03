"""Tests for startSession comment field type acceptance."""

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
from documentdb_tests.framework.property_checks import Eq

# Property [comment Type Acceptance]: the comment field accepts any BSON type.
STARTSESSION_COMMENT_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"comment_{tid}",
        command=lambda ctx, v=val: {"startSession": 1, "comment": v},
        expected={"ok": Eq(1.0)},
        msg=f"startSession should accept {tid} as comment value",
    )
    for tid, val in [
        ("string", "test comment"),
        ("empty_string", ""),
        ("int32", 42),
        ("int64", Int64(123)),
        ("double", 3.14),
        ("decimal128", Decimal128("1.5")),
        ("bool_true", True),
        ("bool_false", False),
        ("null", None),
        ("object", {"key": "value"}),
        ("empty_object", {}),
        ("array", [1, "two", 3.0]),
        ("empty_array", []),
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


@pytest.mark.parametrize("test", pytest_params(STARTSESSION_COMMENT_TYPE_TESTS))
def test_startSession_comment(database_client, collection, test):
    """Test startSession comment field type acceptance."""
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
