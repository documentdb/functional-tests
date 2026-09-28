"""Tests for planCacheClear command query and comment field type acceptance."""

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

# Property [Query Type Acceptance]: the query field accepts all BSON types
# without type validation. Every type succeeds with ok: 1.0.
PLANCACHECLEAR_QUERY_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"query_type_{tid}",
        command=lambda ctx, v=val: {
            "planCacheClear": ctx.collection,
            "query": v,
        },
        expected={"ok": 1.0},
        msg=f"planCacheClear should accept {tid} as query field",
    )
    for tid, val in [
        ("document", {"a": 1}),
        ("empty_document", {}),
        ("string", "hello"),
        ("int", 123),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("decimal128", Decimal128("1")),
        ("bool_true", True),
        ("bool_false", False),
        ("null", None),
        ("array", [1, 2]),
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

# Property [Comment Type Acceptance]: comment field accepts any valid BSON type.
PLANCACHECLEAR_COMMENT_TYPE_ACCEPTANCE_TESTS: list[CommandTestCase] = [
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

PLANCACHECLEAR_QUERY_COMMENT_TYPE_TESTS: list[CommandTestCase] = (
    PLANCACHECLEAR_QUERY_TYPE_TESTS + PLANCACHECLEAR_COMMENT_TYPE_ACCEPTANCE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(PLANCACHECLEAR_QUERY_COMMENT_TYPE_TESTS))
def test_planCacheClear_query_comment_type(database_client, collection, test):
    """Test planCacheClear command query and comment field type acceptance."""
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
