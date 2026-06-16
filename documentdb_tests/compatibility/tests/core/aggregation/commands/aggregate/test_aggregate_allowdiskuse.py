"""Tests for aggregate command allowDiskUse parameter."""

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
from documentdb_tests.framework.error_codes import (
    QUERY_EXCEEDED_MEMORY_NO_DISK_USE_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists
from documentdb_tests.framework.target_collection import ViewCollection

# Property [allowDiskUse Acceptance]: valid allowDiskUse values are accepted
# across all aggregate modes.
AGGREGATE_ALLOWDISKUSE_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "allowdiskuse_true",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "allowDiskUse": True,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept allowDiskUse=true",
    ),
    CommandTestCase(
        "allowdiskuse_false",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "allowDiskUse": False,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept allowDiskUse=false",
    ),
    CommandTestCase(
        "allowdiskuse_true_empty_pipeline",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "allowDiskUse": True,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept allowDiskUse=true with an empty pipeline",
    ),
    CommandTestCase(
        "allowdiskuse_true_explain",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "explain": True,
            "allowDiskUse": True,
        },
        expected={"ok": Eq(1.0), "queryPlanner": Exists()},
        msg="aggregate should accept allowDiskUse=true with explain mode",
    ),
    CommandTestCase(
        "allowdiskuse_true_nonexistent",
        docs=None,
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "allowDiskUse": True,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept allowDiskUse=true on a nonexistent collection",
    ),
    CommandTestCase(
        "allowdiskuse_true_view",
        target_collection=ViewCollection(),
        docs=[],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "allowDiskUse": True,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept allowDiskUse=true on a view",
    ),
    CommandTestCase(
        "allowdiskuse_true_agnostic",
        command={
            "aggregate": 1,
            "pipeline": [{"$documents": [{"x": 1}]}],
            "cursor": {},
            "allowDiskUse": True,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept allowDiskUse=true in collection-agnostic mode",
    ),
    CommandTestCase(
        "allowdiskuse_true_memory_exceeded",
        docs=[{"_id": i, "data": "x" * 100_000, "sort_key": 1050 - i} for i in range(1050)],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"sort_key": 1}}],
            "cursor": {},
            "allowDiskUse": True,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should allow sort exceeding memory limit when allowDiskUse=true",
    ),
]

# Property [allowDiskUse Rejection]: invalid types for allowDiskUse are
# rejected and the memory limit is enforced when disabled.
AGGREGATE_ALLOWDISKUSE_REJECTION_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            f"allowdiskuse_reject_{tid}",
            command=lambda ctx, v=val: {
                "aggregate": ctx.collection,
                "pipeline": [],
                "cursor": {},
                "allowDiskUse": v,
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"aggregate should reject {tid} for allowDiskUse",
        )
        for tid, val in [
            ("null", None),
            ("int32_0", 0),
            ("int32_1", 1),
            ("int64", Int64(1)),
            ("double", 1.0),
            ("decimal128", Decimal128("1")),
            ("string", "true"),
            ("array", [True]),
            ("document", {"x": True}),
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
    CommandTestCase(
        "allowdiskuse_reject_memory_exceeded",
        docs=[{"_id": i, "data": "x" * 100_000, "sort_key": 1050 - i} for i in range(1050)],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"sort_key": 1}}],
            "cursor": {},
            "allowDiskUse": False,
        },
        error_code=QUERY_EXCEEDED_MEMORY_NO_DISK_USE_ERROR,
        msg="aggregate should reject sort exceeding memory limit when allowDiskUse=false",
    ),
]

AGGREGATE_ALLOWDISKUSE_TESTS = (
    AGGREGATE_ALLOWDISKUSE_ACCEPTANCE_TESTS + AGGREGATE_ALLOWDISKUSE_REJECTION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_ALLOWDISKUSE_TESTS))
def test_aggregate_allowdiskuse(database_client, collection, test):
    """Test aggregate allowDiskUse acceptance and rejection."""
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
