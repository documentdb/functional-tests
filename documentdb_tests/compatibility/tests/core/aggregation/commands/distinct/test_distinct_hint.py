"""Tests for distinct command hint parameter behavior."""

from __future__ import annotations

from typing import Any

import pytest
from bson import Decimal128, Int64
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import ViewCollection

# Property [Hint Success]: valid hint values are accepted and influence index
# selection for the distinct command.
DISTINCT_HINT_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "hint_string_matches_index_name",
        indexes=[IndexModel([("x", 1)], name="x_1")],
        docs=[{"_id": 1, "x": "a"}, {"_id": 2, "x": "b"}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x", "hint": "x_1"},
        expected={"values": ["a", "b"], "ok": 1.0},
        msg="distinct should accept a string hint that exactly matches an index name",
    ),
    CommandTestCase(
        "hint_doc_matches_key_pattern",
        indexes=[IndexModel([("x", 1)])],
        docs=[{"_id": 1, "x": "a"}, {"_id": 2, "x": "b"}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x", "hint": {"x": 1}},
        expected={"values": ["a", "b"], "ok": 1.0},
        msg="distinct should accept a document hint matching the index key pattern",
    ),
    CommandTestCase(
        "hint_doc_direction_int64",
        indexes=[IndexModel([("x", 1)])],
        docs=[{"_id": 1, "x": "a"}, {"_id": 2, "x": "b"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "hint": {"x": Int64(1)},
        },
        expected={"values": ["a", "b"], "ok": 1.0},
        msg="distinct should accept Int64(1) as a direction value in document hint",
    ),
    CommandTestCase(
        "hint_doc_direction_double",
        indexes=[IndexModel([("x", 1)])],
        docs=[{"_id": 1, "x": "a"}, {"_id": 2, "x": "b"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "hint": {"x": 1.0},
        },
        expected={"values": ["a", "b"], "ok": 1.0},
        msg="distinct should accept double 1.0 as a direction value in document hint",
    ),
    CommandTestCase(
        "hint_doc_direction_decimal128",
        indexes=[IndexModel([("x", 1)])],
        docs=[{"_id": 1, "x": "a"}, {"_id": 2, "x": "b"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "hint": {"x": Decimal128("1")},
        },
        expected={"values": ["a", "b"], "ok": 1.0},
        msg="distinct should accept Decimal128('1') as a direction value in document hint",
    ),
    CommandTestCase(
        "hint_doc_direction_neg1_int64",
        indexes=[IndexModel([("x", -1)])],
        docs=[{"_id": 1, "x": "a"}, {"_id": 2, "x": "b"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "hint": {"x": Int64(-1)},
        },
        expected={"values": ["a", "b"], "ok": 1.0},
        msg="distinct should accept Int64(-1) as a direction value in document hint",
    ),
    CommandTestCase(
        "hint_doc_direction_neg1_double",
        indexes=[IndexModel([("x", -1)])],
        docs=[{"_id": 1, "x": "a"}, {"_id": 2, "x": "b"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "hint": {"x": -1.0},
        },
        expected={"values": ["a", "b"], "ok": 1.0},
        msg="distinct should accept double -1.0 as a direction value in document hint",
    ),
    CommandTestCase(
        "hint_doc_direction_neg1_decimal128",
        indexes=[IndexModel([("x", -1)])],
        docs=[{"_id": 1, "x": "a"}, {"_id": 2, "x": "b"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "hint": {"x": Decimal128("-1")},
        },
        expected={"values": ["a", "b"], "ok": 1.0},
        msg="distinct should accept Decimal128('-1') as a direction value in document hint",
    ),
    CommandTestCase(
        "hint_doc_direction_neg1_int32",
        indexes=[IndexModel([("x", -1)])],
        docs=[{"_id": 1, "x": "a"}, {"_id": 2, "x": "b"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "hint": {"x": -1},
        },
        expected={"values": ["a", "b"], "ok": 1.0},
        msg="distinct should accept int32 -1 as a direction value in document hint",
    ),
    CommandTestCase(
        "hint_natural_forward",
        docs=[{"_id": 1, "x": "a"}, {"_id": 2, "x": "b"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "hint": {"$natural": 1},
        },
        expected={"values": ["a", "b"], "ok": 1.0},
        msg="distinct should accept $natural: 1 for forward collection scan",
    ),
    CommandTestCase(
        "hint_natural_backward",
        docs=[{"_id": 1, "x": "a"}, {"_id": 2, "x": "b"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "hint": {"$natural": -1},
        },
        expected={"values": ["a", "b"], "ok": 1.0},
        msg="distinct should accept $natural: -1 for backward collection scan",
    ),
    CommandTestCase(
        "hint_empty_doc",
        docs=[{"_id": 1, "x": "a"}, {"_id": 2, "x": "b"}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x", "hint": {}},
        expected={"values": ["a", "b"], "ok": 1.0},
        msg="distinct should treat empty document hint as no hint",
    ),
    CommandTestCase(
        "hint_nonexistent_collection_string",
        docs=None,
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "hint": "any_index_name",
        },
        expected={"values": [], "ok": 1.0},
        msg="distinct should skip hint validation for non-existent collections (string hint)",
    ),
    CommandTestCase(
        "hint_nonexistent_collection_doc",
        docs=None,
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "hint": {"any_field": 1},
        },
        expected={"values": [], "ok": 1.0},
        msg="distinct should skip hint validation for non-existent collections (doc hint)",
    ),
    CommandTestCase(
        "hint_sparse_index",
        indexes=[IndexModel([("y", 1)], sparse=True)],
        docs=[
            {"_id": 1, "x": "a", "y": 1},
            {"_id": 2, "x": "b"},
            {"_id": 3, "x": "c", "y": 3},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x", "hint": {"y": 1}},
        expected={"values": ["a", "c"], "ok": 1.0},
        msg=(
            "distinct with sparse index hint should return only"
            " documents that have the indexed field"
        ),
    ),
    CommandTestCase(
        "hint_partial_index",
        indexes=[
            IndexModel(
                [("x", 1)],
                partialFilterExpression={"status": "active"},
            )
        ],
        docs=[
            {"_id": 1, "x": "a", "status": "active"},
            {"_id": 2, "x": "b", "status": "inactive"},
            {"_id": 3, "x": "c", "status": "active"},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x", "hint": {"x": 1}},
        expected={"values": ["a", "c"], "ok": 1.0},
        msg="distinct with partial index hint should return only documents matching the filter",
    ),
    CommandTestCase(
        "hint_compound_index_by_name",
        indexes=[IndexModel([("x", 1), ("y", 1)], name="x_1_y_1")],
        docs=[{"_id": 1, "x": "a", "y": 1}, {"_id": 2, "x": "b", "y": 2}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x", "hint": "x_1_y_1"},
        expected={"values": ["a", "b"], "ok": 1.0},
        msg="distinct should accept a compound index hint by name",
    ),
    CommandTestCase(
        "hint_compound_index_by_pattern",
        indexes=[IndexModel([("x", 1), ("y", 1)])],
        docs=[{"_id": 1, "x": "a", "y": 1}, {"_id": 2, "x": "b", "y": 2}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "hint": {"x": 1, "y": 1},
        },
        expected={"values": ["a", "b"], "ok": 1.0},
        msg="distinct should accept a compound index hint by key pattern",
    ),
    CommandTestCase(
        "hint_id_index_by_name",
        docs=[{"_id": 1, "x": "a"}, {"_id": 2, "x": "b"}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x", "hint": "_id_"},
        expected={"values": ["a", "b"], "ok": 1.0},
        msg="distinct should accept the default _id index hint by name",
    ),
    CommandTestCase(
        "hint_id_index_by_pattern",
        docs=[{"_id": 1, "x": "a"}, {"_id": 2, "x": "b"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "hint": {"_id": 1},
        },
        expected={"values": ["a", "b"], "ok": 1.0},
        msg="distinct should accept the default _id index hint by key pattern",
    ),
    CommandTestCase(
        "hint_non_collation_compatible_index",
        indexes=[IndexModel([("x", 1)], collation={"locale": "fr"})],
        docs=[{"_id": 1, "x": "a"}, {"_id": 2, "x": "A"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "hint": {"x": 1},
            "collation": {"locale": "en", "strength": 1},
        },
        expected={"values": ["a"], "ok": 1.0},
        msg=(
            "distinct should accept hint referencing a non-collation-compatible"
            " index when collation is specified"
        ),
    ),
]

# Property [Hint Accepted on Views]: hint is accepted on views without error.
DISTINCT_HINT_VIEW_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "hint_accepted_on_view",
        target_collection=ViewCollection(),
        indexes=[IndexModel([("x", 1)])],
        docs=[{"_id": 1, "x": "a"}, {"_id": 2, "x": "b"}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x", "hint": {"x": 1}},
        expected={"values": sorted(["a", "b"]), "ok": 1},
        ignore_order_in=["values"],
        msg="distinct should accept hint on views without error",
    ),
]

DISTINCT_HINT_TESTS: list[CommandTestCase] = DISTINCT_HINT_SUCCESS_TESTS + DISTINCT_HINT_VIEW_TESTS


@pytest.mark.parametrize("test", pytest_params(DISTINCT_HINT_TESTS))
def test_distinct_hint(database_client: Any, collection: Any, test: CommandTestCase) -> None:
    """Test distinct hint cases."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
        ignore_order_in=test.ignore_order_in,
    )
