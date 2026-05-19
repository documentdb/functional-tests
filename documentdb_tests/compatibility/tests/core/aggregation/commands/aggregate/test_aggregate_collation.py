"""Tests for aggregate command collation parameter."""

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
from documentdb_tests.framework.target_collection import CustomCollection, SiblingCollection

# Property [Collation Acceptance]: valid collation values are accepted and
# propagate to string comparisons throughout the pipeline.
AGGREGATE_COLLATION_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collation_null",
        docs=[{"_id": 1, "name": "abc"}, {"_id": 2, "name": "ABC"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"name": "abc"}}],
            "cursor": {},
            "collation": None,
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "name": "abc"}])},
        },
        msg="aggregate should accept null collation and use binary comparison",
    ),
    CommandTestCase(
        "collation_empty_doc",
        docs=[{"_id": 1, "name": "abc"}, {"_id": 2, "name": "ABC"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"name": "abc"}}],
            "cursor": {},
            "collation": {},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "name": "abc"}])},
        },
        msg="aggregate should accept empty document collation and use binary comparison",
    ),
    CommandTestCase(
        "collation_omitted",
        docs=[{"_id": 1, "name": "abc"}, {"_id": 2, "name": "ABC"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"name": "abc"}}],
            "cursor": {},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "name": "abc"}])},
        },
        msg="aggregate should use binary comparison when collation is omitted",
    ),
    CommandTestCase(
        "collation_default_applied",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[{"_id": 1, "name": "abc"}, {"_id": 2, "name": "ABC"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"name": "abc"}}],
            "cursor": {},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "name": "abc"}, {"_id": 2, "name": "ABC"}])},
        },
        msg="aggregate should apply collection default collation when none is specified",
    ),
    CommandTestCase(
        "collation_null_uses_default",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[{"_id": 1, "name": "abc"}, {"_id": 2, "name": "ABC"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"name": "abc"}}],
            "cursor": {},
            "collation": None,
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "name": "abc"}, {"_id": 2, "name": "ABC"}])},
        },
        msg="aggregate should use collection default collation when explicit null is provided",
    ),
    CommandTestCase(
        "collation_empty_doc_uses_default",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[{"_id": 1, "name": "abc"}, {"_id": 2, "name": "ABC"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"name": "abc"}}],
            "cursor": {},
            "collation": {},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "name": "abc"}, {"_id": 2, "name": "ABC"}])},
        },
        msg="aggregate should use collection default collation when empty doc is provided",
    ),
    CommandTestCase(
        "collation_explicit_override",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[{"_id": 1, "name": "abc"}, {"_id": 2, "name": "ABC"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"name": "abc"}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 3},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "name": "abc"}])},
        },
        msg="aggregate should override collection default collation with explicit collation",
    ),
    CommandTestCase(
        "collation_lookup_propagation",
        docs=[{"_id": 1, "key": "abc"}],
        siblings=[
            SiblingCollection(
                suffix="_lookup_target",
                docs=[{"_id": 10, "fk": "ABC"}],
            ),
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$lookup": {
                        "from": f"{ctx.collection}_lookup_target",
                        "localField": "key",
                        "foreignField": "fk",
                        "as": "joined",
                    }
                }
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([{"_id": 1, "key": "abc", "joined": [{"_id": 10, "fk": "ABC"}]}])
            },
        },
        msg="aggregate should propagate command-level collation to $lookup join comparisons",
    ),
    CommandTestCase(
        "collation_graphlookup_propagation",
        docs=[
            {"_id": 1, "name": "abc", "parent": None},
            {"_id": 2, "name": "DEF", "parent": "ABC"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$match": {"_id": 1}},
                {
                    "$graphLookup": {
                        "from": ctx.collection,
                        "startWith": "$name",
                        "connectFromField": "name",
                        "connectToField": "parent",
                        "as": "chain",
                    }
                },
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq(
                    [
                        {
                            "_id": 1,
                            "name": "abc",
                            "parent": None,
                            "chain": [{"_id": 2, "name": "DEF", "parent": "ABC"}],
                        }
                    ]
                )
            },
        },
        msg="aggregate should propagate command-level collation to $graphLookup comparisons",
    ),
    CommandTestCase(
        "collation_lookup_target_default_not_used",
        docs=[{"_id": 1, "key": "abc"}],
        siblings=[
            SiblingCollection(
                suffix="_collated_target",
                collation={"locale": "en", "strength": 2},
                docs=[{"_id": 10, "fk": "ABC"}],
            ),
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$lookup": {
                        "from": f"{ctx.collection}_collated_target",
                        "localField": "key",
                        "foreignField": "fk",
                        "as": "joined",
                    }
                }
            ],
            "cursor": {},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "key": "abc", "joined": []}])},
        },
        msg="aggregate should not use target collection default collation for $lookup joins",
    ),
    CommandTestCase(
        "collation_locale_simple",
        docs=[{"_id": 1, "name": "abc"}, {"_id": 2, "name": "ABC"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"name": "abc"}}],
            "cursor": {},
            "collation": {"locale": "simple"},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "name": "abc"}])},
        },
        msg="aggregate should accept locale 'simple' for explicit binary collation",
    ),
    CommandTestCase(
        "collation_sort_propagation",
        docs=[{"_id": 1, "name": "b"}, {"_id": 2, "name": "A"}, {"_id": 3, "name": "a"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"name": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "caseFirst": "lower"},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq(
                    [{"_id": 3, "name": "a"}, {"_id": 2, "name": "A"}, {"_id": 1, "name": "b"}]
                )
            },
        },
        msg="aggregate should propagate command-level collation to $sort stage",
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
