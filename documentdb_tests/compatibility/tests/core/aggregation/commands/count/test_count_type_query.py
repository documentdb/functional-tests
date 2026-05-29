"""Tests for count command query type strictness."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Type Strictness: query]: only document (object) type is accepted
# for the query field (in addition to null); all other BSON types produce a
# TypeMismatch error.
COUNT_TYPE_STRICTNESS_QUERY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"type_query_{tid}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {"count": ctx.collection, "query": v},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"count should reject {tid} for query field",
    )
    for tid, val in [
        ("string", "invalid"),
        ("int32", 42),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("bool", True),
        ("array", [1, 2]),
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


@pytest.mark.parametrize("test", pytest_params(COUNT_TYPE_STRICTNESS_QUERY_TESTS))
def test_count_type_query(database_client, collection, test):
    """Test count command query type strictness."""
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
