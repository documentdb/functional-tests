"""Tests for aggregate command writeConcern j sub-field."""

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

# Property [writeConcern Sub-field j Acceptance]: j accepts bool, int, long,
# double, and decimal types.
AGGREGATE_WRITECONCERN_J_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wc_j_bool_true",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"j": True},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept j=True in writeConcern",
    ),
    CommandTestCase(
        "wc_j_bool_false",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"j": False},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept j=False in writeConcern",
    ),
    CommandTestCase(
        "wc_j_int_1",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"j": 1},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept j=1 (int32) in writeConcern",
    ),
    CommandTestCase(
        "wc_j_int_0",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"j": 0},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept j=0 (int32) in writeConcern",
    ),
    CommandTestCase(
        "wc_j_int64",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"j": Int64(1)},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept j=Int64(1) in writeConcern",
    ),
    CommandTestCase(
        "wc_j_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"j": 1.0},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept j=1.0 (double) in writeConcern",
    ),
    CommandTestCase(
        "wc_j_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"j": Decimal128("1")},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept j=Decimal128('1') in writeConcern",
    ),
    CommandTestCase(
        "wc_j_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"j": None},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept j=null in writeConcern",
    ),
]

# Property [writeConcern Sub-field j Rejection]: non-boolean, non-numeric
# types for j produce a type mismatch error.
AGGREGATE_WRITECONCERN_J_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"wc_j_reject_{tid}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"j": v},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"aggregate should reject {tid} j in writeConcern",
    )
    for tid, val in [
        ("string", "true"),
        ("array", [1]),
        ("object", {"a": 1}),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("regex", Regex(".*")),
        ("binary", Binary(b"data")),
        ("code", Code("function(){}")),
        ("code_with_scope", Code("function(){}", {"x": 1})),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

AGGREGATE_WRITECONCERN_J_TESTS = (
    AGGREGATE_WRITECONCERN_J_ACCEPTANCE_TESTS + AGGREGATE_WRITECONCERN_J_REJECTION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_WRITECONCERN_J_TESTS))
def test_aggregate_writeconcern_j(database_client, collection, test):
    """Test aggregate writeConcern j sub-field."""
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
