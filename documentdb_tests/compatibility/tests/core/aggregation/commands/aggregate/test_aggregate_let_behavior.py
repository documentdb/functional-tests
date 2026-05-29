"""Tests for aggregate command let variable behavior."""

from __future__ import annotations

import pytest
from bson.son import SON

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.target_collection import SiblingCollection

# Property [Let Variable Behavior]: let variables propagate to sub-pipelines,
# support duplicate resolution, override, and evaluation semantics.
AGGREGATE_LET_BEHAVIOR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "let_later_refs_earlier",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$addFields": {"y": "$$b"}}],
            "cursor": {},
            "let": SON([("a", 10), ("b", "$$a")]),
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "y": 10}])},
        },
        msg="aggregate should allow later let variables to reference earlier ones",
    ),
    CommandTestCase(
        "let_duplicate_last_wins",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$addFields": {"y": "$$myVar"}}],
            "cursor": {},
            "let": SON([("myVar", 1), ("myVar", 2)]),
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "y": 2}])},
        },
        msg="aggregate should use last value when let has duplicate variable names",
    ),
    CommandTestCase(
        "let_override_current",
        docs=[{"_id": 1, "x": "original"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$addFields": {"fromCurrent": "$$CURRENT", "fromRoot": "$$ROOT"}}],
            "cursor": {},
            "let": {"CURRENT": {"overridden": True}},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq(
                    [
                        {
                            "_id": 1,
                            "x": "original",
                            "fromCurrent": {"overridden": True},
                            "fromRoot": {"_id": 1, "x": "original"},
                        }
                    ]
                )
            },
        },
        msg="aggregate should allow overriding CURRENT in let while ROOT remains unaffected",
    ),
    CommandTestCase(
        "let_propagate_lookup",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$lookup": {
                        "from": ctx.collection,
                        "pipeline": [{"$addFields": {"fromLet": "$$myVar"}}],
                        "as": "joined",
                    }
                }
            ],
            "cursor": {},
            "let": {"myVar": "lookup_val"},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([{"_id": 1, "joined": [{"_id": 1, "fromLet": "lookup_val"}]}])
            },
        },
        msg="aggregate should propagate let variables into $lookup sub-pipelines",
    ),
    CommandTestCase(
        "let_propagate_facet",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$facet": {"branch": [{"$addFields": {"fromLet": "$$myVar"}}]}}],
            "cursor": {},
            "let": {"myVar": "facet_val"},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"branch": [{"_id": 1, "fromLet": "facet_val"}]}])},
        },
        msg="aggregate should propagate let variables into $facet sub-pipelines",
    ),
    CommandTestCase(
        "let_propagate_unionwith",
        docs=[{"_id": 1}],
        siblings=[
            SiblingCollection(
                suffix="_union_target",
                docs=[{"_id": 2}],
            ),
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$unionWith": {
                        "coll": f"{ctx.collection}_union_target",
                        "pipeline": [{"$addFields": {"fromLet": "$$myVar"}}],
                    }
                }
            ],
            "cursor": {},
            "let": {"myVar": "union_val"},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1}, {"_id": 2, "fromLet": "union_val"}])},
        },
        msg="aggregate should propagate let variables into $unionWith sub-pipelines",
    ),
    CommandTestCase(
        "let_propagate_nested_lookup",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$lookup": {
                        "from": ctx.collection,
                        "pipeline": [
                            {
                                "$lookup": {
                                    "from": ctx.collection,
                                    "pipeline": [{"$addFields": {"fromLet": "$$myVar"}}],
                                    "as": "inner",
                                }
                            }
                        ],
                        "as": "outer",
                    }
                }
            ],
            "cursor": {},
            "let": {"myVar": "nested"},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq(
                    [
                        {
                            "_id": 1,
                            "outer": [{"_id": 1, "inner": [{"_id": 1, "fromLet": "nested"}]}],
                        }
                    ]
                )
            },
        },
        msg="aggregate should propagate let variables into nested $lookup sub-pipelines",
    ),
    CommandTestCase(
        "let_propagate_merge_when_matched",
        docs=[{"_id": 1, "x": 10}],
        siblings=[
            SiblingCollection(
                suffix="_merge_target",
                docs=[{"_id": 1, "val": "old"}],
            ),
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$merge": {
                        "into": f"{ctx.collection}_merge_target",
                        "on": "_id",
                        "whenMatched": [{"$addFields": {"merged": "$$myVar"}}],
                    }
                }
            ],
            "cursor": {},
            "let": {"myVar": "merge_val"},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should propagate let variables into $merge whenMatched pipeline",
    ),
    CommandTestCase(
        "let_match_with_expr",
        docs=[{"_id": 1, "x": 10}, {"_id": 2, "x": 20}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"$expr": {"$eq": ["$x", "$$threshold"]}}}],
            "cursor": {},
            "let": {"threshold": 10},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "x": 10}])},
        },
        msg="aggregate should allow let variables in $match via $expr",
    ),
    CommandTestCase(
        "let_rand_evaluated_once",
        docs=[{"_id": i} for i in range(3)],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$addFields": {"r": "$$randVal"}},
                {"$group": {"_id": None, "vals": {"$addToSet": "$r"}}},
                {"$project": {"_id": 0, "count": {"$size": "$vals"}}},
            ],
            "cursor": {},
            "let": {"randVal": {"$rand": {}}},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"count": 1}])},
        },
        msg="aggregate should evaluate $rand in let once at parse time",
    ),
    CommandTestCase(
        "let_lookup_shadows_command_let",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$lookup": {
                        "from": ctx.collection,
                        "let": {"myVar": "inner_value"},
                        "pipeline": [{"$addFields": {"fromLet": "$$myVar"}}],
                        "as": "joined",
                    }
                }
            ],
            "cursor": {},
            "let": {"myVar": "outer_value"},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([{"_id": 1, "joined": [{"_id": 1, "fromLet": "inner_value"}]}])
            },
        },
        msg="aggregate should let $lookup let shadow command-level let variable of same name",
    ),
    CommandTestCase(
        "let_lookup_shadow_does_not_affect_outer",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$lookup": {
                        "from": ctx.collection,
                        "let": {"myVar": "inner_value"},
                        "pipeline": [{"$addFields": {"fromLet": "$$myVar"}}],
                        "as": "joined",
                    }
                },
                {"$addFields": {"afterLookup": "$$myVar"}},
            ],
            "cursor": {},
            "let": {"myVar": "outer_value"},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq(
                    [
                        {
                            "_id": 1,
                            "joined": [{"_id": 1, "fromLet": "inner_value"}],
                            "afterLookup": "outer_value",
                        }
                    ]
                )
            },
        },
        msg="aggregate should restore command-level let after $lookup with shadowing let",
    ),
    CommandTestCase(
        "let_lookup_outer_accessible_alongside_inner",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$lookup": {
                        "from": ctx.collection,
                        "let": {"innerVar": "inner_only"},
                        "pipeline": [{"$addFields": {"outer": "$$myVar", "inner": "$$innerVar"}}],
                        "as": "joined",
                    }
                }
            ],
            "cursor": {},
            "let": {"myVar": "outer_value"},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq(
                    [
                        {
                            "_id": 1,
                            "joined": [{"_id": 1, "outer": "outer_value", "inner": "inner_only"}],
                        }
                    ]
                )
            },
        },
        msg="aggregate should allow command-level let to be accessed alongside $lookup let",
    ),
]


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_LET_BEHAVIOR_TESTS))
def test_aggregate_let_behavior(database_client, collection, test):
    """Test aggregate let variable behavior."""
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
