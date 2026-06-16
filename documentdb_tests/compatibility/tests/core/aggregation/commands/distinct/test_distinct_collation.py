"""Tests for distinct command collation field syntax validation."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Collation Acceptance]: the collation field accepts null and
# a document type.
DISTINCT_COLLATION_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collation_null",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x", "collation": None},
        expected={"values": ["a"], "ok": 1.0},
        msg="distinct should accept null collation",
    ),
    CommandTestCase(
        "collation_empty_doc",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x", "collation": {}},
        expected={"values": ["a"], "ok": 1.0},
        msg="distinct should accept empty document collation",
    ),
]

# Property [Collation Type Rejection]: all non-document, non-null BSON types
# for the collation field produce a type mismatch error.
DISTINCT_COLLATION_TYPE_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"collation_type_{tid}",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx, v=val: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": v,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"distinct should reject {tid} as collation",
    )
    for tid, val in [
        ("string", "en"),
        ("int32", 42),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("bool", True),
        ("array", [1, 2]),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"data")),
        ("regex", Regex("abc")),
        ("code", Code("function(){}")),
        ("code_with_scope", Code("function(){}", {"x": 1})),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

DISTINCT_COLLATION_TESTS: list[CommandTestCase] = (
    DISTINCT_COLLATION_ACCEPTANCE_TESTS + DISTINCT_COLLATION_TYPE_REJECTION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(DISTINCT_COLLATION_TESTS))
def test_distinct_collation(database_client, collection, test):
    """Test distinct command collation field syntax validation."""
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
