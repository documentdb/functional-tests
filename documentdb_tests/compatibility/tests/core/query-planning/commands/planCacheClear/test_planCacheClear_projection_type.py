"""Tests for planCacheClear command projection field type acceptance.

MongoDB does not validate the type of the projection field — all BSON types
are silently accepted and the command succeeds.
"""

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

# Property [Projection Type Acceptance]: the projection field accepts all BSON
# types without type validation — every type succeeds with ok: 1.0.
PLANCACHECLEAR_PROJECTION_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"projection_type_{tid}",
        command=lambda ctx, v=val: {
            "planCacheClear": ctx.collection,
            "query": {"a": 1},
            "projection": v,
        },
        expected={"ok": 1.0},
        msg=f"planCacheClear should accept {tid} as projection field",
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


@pytest.mark.parametrize("test", pytest_params(PLANCACHECLEAR_PROJECTION_TYPE_TESTS))
def test_planCacheClear_projection_type(database_client, collection, test):
    """Test planCacheClear command projection field type acceptance."""
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
