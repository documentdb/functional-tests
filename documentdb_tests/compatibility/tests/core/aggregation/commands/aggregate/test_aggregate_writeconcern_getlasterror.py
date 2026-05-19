"""Tests for aggregate command writeConcern getLastError sub-field."""

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

# Property [writeConcern Sub-field getLastError Acceptance]: the legacy
# getLastError field accepts any BSON type and is silently ignored.
AGGREGATE_WRITECONCERN_GETLASTERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"wc_getlasterror_{tid}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"getLastError": v},
        },
        expected={"ok": Eq(1.0)},
        msg=f"aggregate should accept getLastError as {tid}",
    )
    for tid, val in [
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.0),
        ("decimal128", Decimal128("1")),
        ("string", "hello"),
        ("bool", True),
        ("null", None),
        ("array", [1, 2]),
        ("document", {"a": 1}),
        ("binary", Binary(b"data")),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("regex", Regex(".*")),
        ("code", Code("function(){}")),
        ("code_with_scope", Code("function(){}", {"x": 1})),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_WRITECONCERN_GETLASTERROR_TESTS))
def test_aggregate_writeconcern_getlasterror(database_client, collection, test):
    """Test aggregate command writeConcern getLastError sub-field."""
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
