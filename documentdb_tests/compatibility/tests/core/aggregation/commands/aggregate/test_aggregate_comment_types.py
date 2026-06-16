"""Tests for aggregate command comment type acceptance."""

from __future__ import annotations

import uuid
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

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [Comment Type Acceptance]: the comment field accepts all BSON types
# and omission.
AGGREGATE_COMMENT_TYPE_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            f"comment_{tid}",
            docs=[{"_id": 1}],
            command=lambda ctx, v=val: {
                "aggregate": ctx.collection,
                "pipeline": [],
                "cursor": {},
                "comment": v,
            },
            expected={"ok": Eq(1.0)},
            msg=f"aggregate should accept {tid} comment",
        )
        for tid, val in [
            ("string", "hello"),
            ("int32", 42),
            ("int64", Int64(99)),
            ("double", 3.14),
            ("decimal128", Decimal128("1.23")),
            ("bool_true", True),
            ("bool_false", False),
            ("null", None),
            ("array", [1, "two", None]),
            ("document", {"key": "value"}),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("timestamp", Timestamp(1, 1)),
            ("binary", Binary(b"hello")),
            ("binary_uuid", Binary.from_uuid(uuid.uuid4())),
            ("regex", Regex(".*", "i")),
            ("code", Code("function(){}")),
            ("code_with_scope", Code("function(){}", {"x": 1})),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    CommandTestCase(
        "comment_omitted",
        docs=[{"_id": 1}],
        command=lambda ctx: {"aggregate": ctx.collection, "pipeline": [], "cursor": {}},
        expected={"ok": Eq(1.0)},
        msg="aggregate should succeed when comment is omitted",
    ),
]


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_COMMENT_TYPE_TESTS))
def test_aggregate_comment_types(database_client, collection, test):
    """Test aggregate comment type acceptance."""
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
