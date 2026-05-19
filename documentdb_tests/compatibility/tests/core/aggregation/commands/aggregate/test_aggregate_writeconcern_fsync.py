"""Tests for aggregate command writeConcern fsync sub-field."""

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
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [writeConcern Sub-field fsync Acceptance]: fsync accepts bool,
# numeric, and null types.
AGGREGATE_WRITECONCERN_FSYNC_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wc_fsync_bool_true",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"fsync": True},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept fsync=True in writeConcern",
    ),
    CommandTestCase(
        "wc_fsync_bool_false",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"fsync": False},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept fsync=False in writeConcern",
    ),
    CommandTestCase(
        "wc_fsync_int_1",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"fsync": 1},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept fsync=1 (int32) in writeConcern",
    ),
    CommandTestCase(
        "wc_fsync_int_0",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"fsync": 0},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept fsync=0 (int32) in writeConcern",
    ),
    CommandTestCase(
        "wc_fsync_int64",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"fsync": Int64(1)},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept fsync=Int64(1) in writeConcern",
    ),
    CommandTestCase(
        "wc_fsync_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"fsync": 1.0},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept fsync=1.0 (double) in writeConcern",
    ),
    CommandTestCase(
        "wc_fsync_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"fsync": Decimal128("1")},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept fsync=Decimal128('1') in writeConcern",
    ),
    CommandTestCase(
        "wc_fsync_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"fsync": None},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept fsync=null in writeConcern",
    ),
]

# Property [writeConcern Sub-field fsync Rejection]: non-boolean, non-numeric
# types for fsync produce a type mismatch error.
AGGREGATE_WRITECONCERN_FSYNC_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"wc_fsync_reject_{tid}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"fsync": v},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"aggregate should reject {tid} fsync in writeConcern",
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

AGGREGATE_WRITECONCERN_FSYNC_TESTS = (
    AGGREGATE_WRITECONCERN_FSYNC_ACCEPTANCE_TESTS + AGGREGATE_WRITECONCERN_FSYNC_REJECTION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_WRITECONCERN_FSYNC_TESTS))
def test_aggregate_writeconcern_fsync(database_client, collection, test):
    """Test aggregate writeConcern fsync sub-field."""
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
