"""Tests for aggregate command collation parameter syntax validation."""

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

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [Collation Acceptance]: the collation field accepts null and
# a document type.
AGGREGATE_COLLATION_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collation_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": None,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept null collation",
    ),
    CommandTestCase(
        "collation_empty_doc",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept empty document collation",
    ),
]

# Property [Collation Type Rejection]: all non-document, non-null BSON types
# for the collation field produce a type mismatch error.
AGGREGATE_COLLATION_TYPE_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"collation_type_{tid}",
        command=lambda ctx, v=val: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": v,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"aggregate should reject {tid} collation",
    )
    for tid, val in [
        ("bool", True),
        ("int", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("decimal128", Decimal128("1")),
        ("string", "en"),
        ("array", [{"locale": "en"}]),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"data")),
        ("regex", Regex(".*")),
        ("code", Code("function(){}")),
        ("code_with_scope", Code("function(){}", {"x": 1})),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

AGGREGATE_COLLATION_TESTS = (
    AGGREGATE_COLLATION_ACCEPTANCE_TESTS + AGGREGATE_COLLATION_TYPE_REJECTION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_COLLATION_TESTS))
def test_aggregate_collation(database_client, collection, test):
    """Test aggregate collation acceptance and rejection."""
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
