"""Tests for count command field type strictness."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import INVALID_NAMESPACE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Type Strictness: count]: only string type is accepted for the count
# field; all non-string types produce an invalid namespace error.
COUNT_TYPE_STRICTNESS_COUNT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "type_count_string_valid",
        docs=None,
        command=lambda ctx: {"count": ctx.collection},
        expected={"n": 0, "ok": 1.0},
        msg="count should accept a string collection name",
    ),
    *[
        CommandTestCase(
            f"type_count_{tid}",
            docs=None,
            command=lambda ctx, v=val: {"count": v},
            error_code=INVALID_NAMESPACE_ERROR,
            msg=f"count should reject {tid} for collection name",
        )
        for tid, val in [
            ("int32", 42),
            ("int64", Int64(1)),
            ("double", 3.14),
            ("decimal128", Decimal128("1")),
            ("bool", True),
            ("null", None),
            ("array", [1, 2]),
            ("object", {"a": 1}),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("timestamp", Timestamp(1, 1)),
            ("binary_generic", Binary(b"\x01\x02\x03")),
            ("regex", Regex("^abc")),
            ("code", Code("function(){}")),
            ("code_with_scope", Code("function(){}", {"x": 1})),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
]


@pytest.mark.parametrize("test", pytest_params(COUNT_TYPE_STRICTNESS_COUNT_TESTS))
def test_count_namespace(database_client, collection, test):
    """Test count command field type strictness."""
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
