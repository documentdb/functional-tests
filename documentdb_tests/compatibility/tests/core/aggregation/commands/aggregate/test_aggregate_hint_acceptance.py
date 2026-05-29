"""Tests for aggregate command hint parameter acceptance."""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.test_constants import DECIMAL128_TRAILING_ZERO

# Property [Hint String Name Matching]: string and document hints matching
# existing index names or specifications are accepted.
AGGREGATE_HINT_NAME_MATCHING_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "hint_string_name",
        docs=[{"_id": 1, "x": 10}],
        indexes=[IndexModel([("x", 1)], name="x_1")],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": "x_1",
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept a string hint matching an existing index name",
    ),
    CommandTestCase(
        "hint_document_spec",
        docs=[{"_id": 1, "x": 10}],
        indexes=[IndexModel([("x", 1)], name="x_1")],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": {"x": 1},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept a document hint matching an index specification",
    ),
    CommandTestCase(
        "hint_string_case_sensitive",
        docs=[{"_id": 1, "x": 10}],
        indexes=[IndexModel([("x", 1)], name="MyIndex")],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": "MyIndex",
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should match index name case-sensitively",
    ),
    CommandTestCase(
        "hint_string_special_chars",
        docs=[{"_id": 1, "x": 10}],
        indexes=[IndexModel([("x", 1)], name="my idx $special.name")],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": "my idx $special.name",
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept special characters in index name hint",
    ),
    CommandTestCase(
        "hint_string_unicode",
        docs=[{"_id": 1, "x": 10}],
        indexes=[IndexModel([("x", 1)], name="idx_\u00e9\u4e2d")],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": "idx_\u00e9\u4e2d",
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept unicode characters in index name hint",
    ),
]

# Property [Hint Direction Type Coercion]: document hints accept Int64, double,
# and Decimal128 direction values that resolve to 1 or -1.
AGGREGATE_HINT_DIRECTION_COERCION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "hint_doc_direction_int64",
        docs=[{"_id": 1, "x": 10}],
        indexes=[IndexModel([("x", -1)], name="x_neg1")],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": {"x": Int64(-1)},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept Int64 direction value in document hint",
    ),
    CommandTestCase(
        "hint_doc_direction_double",
        docs=[{"_id": 1, "x": 10}],
        indexes=[IndexModel([("x", -1)], name="x_neg1")],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": {"x": -1.0},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept double direction value in document hint",
    ),
    CommandTestCase(
        "hint_doc_direction_decimal128",
        docs=[{"_id": 1, "x": 10}],
        indexes=[IndexModel([("x", -1)], name="x_neg1")],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": {"x": Decimal128("-1")},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept Decimal128 direction value in document hint",
    ),
    CommandTestCase(
        "hint_doc_direction_decimal128_trailing_zeros",
        docs=[{"_id": 1, "x": 10}],
        indexes=[IndexModel([("x", 1)], name="x_1")],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": {"x": DECIMAL128_TRAILING_ZERO},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept Decimal128 with trailing zeros in document hint",
    ),
    CommandTestCase(
        "hint_doc_direction_decimal128_scientific",
        docs=[{"_id": 1, "x": 10}],
        indexes=[IndexModel([("x", -1)], name="x_neg1")],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": {"x": Decimal128("-1E0")},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept Decimal128 scientific notation in document hint",
    ),
]

# Property [Hint $natural]: $natural forward and reverse hints are accepted.
AGGREGATE_HINT_NATURAL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "hint_natural_forward",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": {"$natural": 1},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept $natural forward hint",
    ),
    CommandTestCase(
        "hint_natural_reverse",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": {"$natural": -1},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept $natural reverse hint",
    ),
]

# Property [Hint Non-Existent Collection]: any hint is accepted when the
# target collection does not exist.
AGGREGATE_HINT_NONEXISTENT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "hint_nonexistent_collection_string",
        docs=None,
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": "fake_index",
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept any string hint on a non-existent collection",
    ),
    CommandTestCase(
        "hint_nonexistent_collection_document",
        docs=None,
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": {"a": 1},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept any document hint on a non-existent collection",
    ),
]

# Property [Hint Stage Interactions]: hint is accepted alongside $lookup,
# $graphLookup, $out, and $merge without propagating to sub-pipelines.
AGGREGATE_HINT_STAGE_INTERACTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "hint_with_lookup_no_propagation",
        docs=[{"_id": 1, "x": 1}],
        indexes=[IndexModel([("x", 1)], name="x_1")],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$lookup": {
                        "from": ctx.collection,
                        "localField": "x",
                        "foreignField": "x",
                        "as": "joined",
                    }
                }
            ],
            "cursor": {},
            "hint": "x_1",
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should validate hint against initial collection only, not lookup target",
    ),
    CommandTestCase(
        "hint_with_graphlookup_no_propagation",
        docs=[{"_id": 1, "x": 1, "to": 2}, {"_id": 2, "x": 2, "to": 3}],
        indexes=[IndexModel([("x", 1)], name="x_1")],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$graphLookup": {
                        "from": ctx.collection,
                        "startWith": "$to",
                        "connectFromField": "to",
                        "connectToField": "x",
                        "as": "connected",
                    }
                }
            ],
            "cursor": {},
            "hint": "x_1",
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should validate hint against initial collection only, not graphLookup",
    ),
]

# Property [Hint Index Type Behavior]: sparse and partial filter indexes
# restrict results when used as hints.
AGGREGATE_HINT_INDEX_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "hint_sparse_index_restricts",
        docs=[
            {"_id": 1, "x": 1, "s": "a"},
            {"_id": 2, "x": 2},
            {"_id": 3, "x": 3, "s": "b"},
        ],
        indexes=[IndexModel([("s", 1)], name="s_sparse", sparse=True)],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": "s_sparse",
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([{"_id": 1, "x": 1, "s": "a"}, {"_id": 3, "x": 3, "s": "b"}]),
            },
        },
        msg="aggregate should restrict results to indexed documents when using sparse index hint",
    ),
    CommandTestCase(
        "hint_partial_filter_restricts",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 5}, {"_id": 3, "x": 10}],
        indexes=[
            IndexModel(
                [("x", 1)],
                name="x_partial",
                partialFilterExpression={"x": {"$gte": 5}},
            )
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": "x_partial",
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([{"_id": 2, "x": 5}, {"_id": 3, "x": 10}]),
            },
        },
        msg="aggregate should restrict results to documents matching partial filter with hint",
    ),
    CommandTestCase(
        "hint_with_out",
        docs=[{"_id": 1, "x": 10}],
        indexes=[IndexModel([("x", 1)], name="x_1")],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$out": "hint_out_target"}],
            "cursor": {},
            "hint": "x_1",
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept hint with $out pipeline",
    ),
    CommandTestCase(
        "hint_with_merge",
        docs=[{"_id": 1, "x": 10}],
        indexes=[IndexModel([("x", 1)], name="x_1")],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$merge": {"into": "hint_merge_target"}}],
            "cursor": {},
            "hint": "x_1",
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept hint with $merge pipeline",
    ),
]

AGGREGATE_HINT_ACCEPTANCE_TESTS = (
    AGGREGATE_HINT_NAME_MATCHING_TESTS
    + AGGREGATE_HINT_DIRECTION_COERCION_TESTS
    + AGGREGATE_HINT_NATURAL_TESTS
    + AGGREGATE_HINT_NONEXISTENT_TESTS
    + AGGREGATE_HINT_STAGE_INTERACTION_TESTS
    + AGGREGATE_HINT_INDEX_TYPE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_HINT_ACCEPTANCE_TESTS))
def test_aggregate_hint_acceptance(database_client, collection, test):
    """Test aggregate hint acceptance."""
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
