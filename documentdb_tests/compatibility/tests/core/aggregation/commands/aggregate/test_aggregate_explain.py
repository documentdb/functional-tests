"""Tests for aggregate command explain parameter."""

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
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    FAILED_TO_PARSE_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists

# Property [Explain Acceptance]: explain=true produces query plan output
# with the correct response shape.
AGGREGATE_EXPLAIN_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "explain_true_no_cursor",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {"aggregate": ctx.collection, "pipeline": [], "explain": True},
        expected={
            "ok": Eq(1.0),
            "queryPlanner": Exists(),
            "explainVersion": Exists(),
            "command": Exists(),
            "serverInfo": Exists(),
            "serverParameters": Exists(),
            "queryShapeHash": Exists(),
        },
        msg="aggregate should return query plan info with explain=true and no cursor",
    ),
    CommandTestCase(
        "explain_true_with_cursor",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "explain": True,
        },
        expected={
            "ok": Eq(1.0),
            "queryPlanner": Exists(),
            "explainVersion": Exists(),
            "command": Exists(),
            "serverInfo": Exists(),
            "serverParameters": Exists(),
            "queryShapeHash": Exists(),
        },
        msg="aggregate should return query plan info with explain=true and cursor present",
    ),
    CommandTestCase(
        "explain_false_normal_results",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "explain": False,
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([{"_id": 1, "x": 10}]),
            },
        },
        msg="aggregate should produce normal results with explain=false",
    ),
    CommandTestCase(
        "explain_out_stages_format",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$out": "explain_out_target"}],
            "explain": True,
        },
        expected={
            "ok": Eq(1.0),
            "stages": Exists(),
            "explainVersion": Exists(),
            "command": Exists(),
            "serverInfo": Exists(),
            "serverParameters": Exists(),
            "queryShapeHash": Exists(),
        },
        msg="aggregate should use stages format for explain with $out",
    ),
    CommandTestCase(
        "explain_merge_stages_format",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$merge": {"into": "explain_merge_target"}}],
            "explain": True,
        },
        expected={
            "ok": Eq(1.0),
            "stages": Exists(),
            "explainVersion": Exists(),
            "command": Exists(),
            "serverInfo": Exists(),
            "serverParameters": Exists(),
            "queryShapeHash": Exists(),
        },
        msg="aggregate should use stages format for explain with $merge",
    ),
    CommandTestCase(
        "explain_agnostic_stages_format",
        command={
            "aggregate": 1,
            "pipeline": [{"$documents": [{"x": 1}]}],
            "explain": True,
        },
        expected={
            "ok": Eq(1.0),
            "stages": Exists(),
            "explainVersion": Exists(),
            "command": Exists(),
            "serverInfo": Exists(),
            "serverParameters": Exists(),
            "queryShapeHash": Exists(),
        },
        msg="aggregate should use stages format for explain with collection-agnostic pipeline",
    ),
]

# Property [Explain Acceptance Errors]: optimization-time errors and
# parameter validation errors are still raised in explain mode.
AGGREGATE_EXPLAIN_ACCEPTANCE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "explain_optimization_error",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"x": {"$divide": [1, 0]}}}],
            "explain": True,
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should raise optimization-time divide-by-zero error in explain mode",
    ),
    CommandTestCase(
        "explain_allowdiskuse_validation",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "explain": True,
            "allowDiskUse": "yes",
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject invalid allowDiskUse type even with explain=true",
    ),
    CommandTestCase(
        "explain_let_validation",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "explain": True,
            "let": "invalid",
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject invalid let type even with explain=true",
    ),
    CommandTestCase(
        "explain_collation_validation",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "explain": True,
            "collation": 123,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject invalid collation type even with explain=true",
    ),
    CommandTestCase(
        "explain_readconcern_validation",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "explain": True,
            "readConcern": 123,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject invalid readConcern type even with explain=true",
    ),
    CommandTestCase(
        "explain_hint_validation",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "explain": True,
            "hint": 123,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject invalid hint type even with explain=true",
    ),
]

# Property [Explain Rejection]: invalid types for the explain field and
# incompatible parameter combinations are rejected.
AGGREGATE_EXPLAIN_REJECTION_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            f"explain_reject_{tid}",
            command=lambda ctx, v=val: {
                "aggregate": ctx.collection,
                "pipeline": [],
                "cursor": {},
                "explain": v,
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"aggregate should reject {tid} for explain",
        )
        for tid, val in [
            ("null", None),
            ("int_0", 0),
            ("int_1", 1),
            ("double", 1.0),
            ("int64", Int64(1)),
            ("decimal128", Decimal128("1")),
            ("string", "true"),
            ("array", [1, 2]),
            ("document", {"a": 1}),
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
    ],
    *[
        CommandTestCase(
            f"explain_reject_writeconcern_{tid}",
            command=lambda ctx, v=val: {
                "aggregate": ctx.collection,
                "pipeline": [],
                "explain": True,
                "writeConcern": v,
            },
            error_code=FAILED_TO_PARSE_ERROR,
            msg=f"aggregate should reject explain=true with writeConcern {tid}",
        )
        for tid, val in [
            ("empty", {}),
            ("w1", {"w": 1}),
            ("majority", {"w": "majority"}),
        ]
    ],
]

AGGREGATE_EXPLAIN_TESTS = (
    AGGREGATE_EXPLAIN_ACCEPTANCE_TESTS
    + AGGREGATE_EXPLAIN_ACCEPTANCE_ERROR_TESTS
    + AGGREGATE_EXPLAIN_REJECTION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_EXPLAIN_TESTS))
def test_aggregate_explain(database_client, collection, test):
    """Test aggregate explain acceptance and rejection."""
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
