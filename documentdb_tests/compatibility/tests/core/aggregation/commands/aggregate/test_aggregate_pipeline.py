"""Tests for aggregate command pipeline field acceptance."""

from __future__ import annotations

from datetime import datetime, timezone
from functools import reduce

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
from documentdb_tests.framework.error_codes import MISSING_FIELD_ERROR, TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [Pipeline Acceptance]: valid pipeline configurations execute
# successfully and produce correct results.
AGGREGATE_PIPELINE_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "pipeline_empty",
        docs=[{"_id": 1, "x": 10}, {"_id": 2, "x": 20}],
        command=lambda ctx: {"aggregate": ctx.collection, "pipeline": [], "cursor": {}},
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([{"_id": 1, "x": 10}, {"_id": 2, "x": 20}]),
            },
        },
        msg="aggregate should accept an empty pipeline and return all documents",
    ),
    CommandTestCase(
        "pipeline_stages_in_order",
        docs=[{"_id": 1, "x": 10}, {"_id": 2, "x": 20}, {"_id": 3, "x": 30}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$match": {"x": {"$gte": 20}}},
                {"$sort": {"x": -1}},
            ],
            "cursor": {},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 3, "x": 30}, {"_id": 2, "x": 20}])},
        },
        msg="aggregate should execute pipeline stages in order",
    ),
    CommandTestCase(
        "pipeline_1000_stages",
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$addFields": {"x": 1}}] * 1000,
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept up to 1000 stages in a single pipeline",
    ),
    CommandTestCase(
        "pipeline_facet_1000_stages",
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$facet": {"branch": [{"$addFields": {"x": 1}}] * 1000}}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept 1000 stages in a $facet sub-pipeline",
    ),
    CommandTestCase(
        "pipeline_lookup_1000_stages",
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$lookup": {
                        "from": ctx.collection,
                        "pipeline": [{"$addFields": {"x": 1}}] * 1000,
                        "as": "joined",
                    }
                }
            ],
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept 1000 stages in a $lookup sub-pipeline",
    ),
    CommandTestCase(
        "pipeline_unionwith_1000_stages",
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$unionWith": {
                        "coll": ctx.collection,
                        "pipeline": [{"$addFields": {"x": 1}}] * 1000,
                    }
                }
            ],
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept 1000 stages in a $unionWith sub-pipeline",
    ),
    CommandTestCase(
        "pipeline_nesting_depth_20",
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": reduce(
                lambda p, i: [{"$lookup": {"from": ctx.collection, "pipeline": p, "as": f"j{i}"}}],
                range(20),
                [{"$addFields": {"x": 1}}],
            ),
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept sub-pipeline nesting depth of 20 via $lookup",
    ),
    CommandTestCase(
        "pipeline_nesting_depth_20_unionwith",
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": reduce(
                lambda p, _: [{"$unionWith": {"coll": ctx.collection, "pipeline": p}}],
                range(20),
                [{"$addFields": {"x": 1}}],
            ),
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept sub-pipeline nesting depth of 20 via $unionWith",
    ),
]

# Property [Pipeline Type Rejection]: invalid types for the pipeline field
# are rejected.
AGGREGATE_PIPELINE_TYPE_REJECTION_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            f"pipeline_type_{tid}",
            command=lambda ctx, v=val: {"aggregate": ctx.collection, "pipeline": v, "cursor": {}},
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"aggregate should reject {tid} pipeline",
        )
        for tid, val in [
            ("null", None),
            ("bool", True),
            ("int", 1),
            ("int64", Int64(1)),
            ("double", 1.5),
            ("decimal128", Decimal128("1")),
            ("string", "hello"),
            ("document", {"$match": {}}),
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
        "pipeline_missing",
        command=lambda ctx: {"aggregate": ctx.collection, "cursor": {}},
        error_code=MISSING_FIELD_ERROR,
        msg="aggregate should reject missing pipeline field",
    ),
]

AGGREGATE_PIPELINE_TESTS = (
    AGGREGATE_PIPELINE_ACCEPTANCE_TESTS + AGGREGATE_PIPELINE_TYPE_REJECTION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_PIPELINE_TESTS))
def test_aggregate_pipeline(database_client, collection, test):
    """Test aggregate pipeline field acceptance and type rejection."""
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
