"""Tests for capped collection ordering behaviors."""

from __future__ import annotations

import pytest
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import CappedCollection

# Property [Insertion Order]: documents inserted into a capped collection are
# returned in insertion order when queried with find() without an explicit sort.
CAPPED_INSERTION_ORDER_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "order_descending_ids",
        target_collection=CappedCollection(size=100_000),
        docs=[{"_id": 5}, {"_id": 3}, {"_id": 1}, {"_id": 4}],
        command=lambda ctx: {"find": ctx.collection, "projection": {"_id": 1}},
        expected=[{"_id": 5}, {"_id": 3}, {"_id": 1}, {"_id": 4}],
        msg="find() should return documents in insertion order regardless of _id values",
    ),
    CommandTestCase(
        "order_mixed_type_ids",
        target_collection=CappedCollection(size=100_000),
        docs=[
            {"_id": "str"},
            {"_id": 42},
            {"_id": None},
            {"_id": True},
        ],
        command=lambda ctx: {"find": ctx.collection, "projection": {"_id": 1}},
        expected=[
            {"_id": "str"},
            {"_id": 42},
            {"_id": None},
            {"_id": True},
        ],
        msg="find() should preserve insertion order with mixed _id types",
    ),
    CommandTestCase(
        "order_varying_doc_sizes",
        target_collection=CappedCollection(size=100_000),
        docs=[
            {"_id": 3, "data": "x"},
            {"_id": 1, "data": "y" * 100},
            {"_id": 2, "data": "z" * 10},
        ],
        command=lambda ctx: {"find": ctx.collection, "projection": {"_id": 1}},
        expected=[{"_id": 3}, {"_id": 1}, {"_id": 2}],
        msg="find() should preserve insertion order regardless of document sizes",
    ),
    CommandTestCase(
        "filter_preserves_order",
        target_collection=CappedCollection(size=100_000),
        docs=[
            {"_id": 5, "x": "a"},
            {"_id": 2, "x": "b"},
            {"_id": 8, "x": "a"},
            {"_id": 1, "x": "c"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": "a"},
            "projection": {"_id": 1},
        },
        expected=[{"_id": 5}, {"_id": 8}],
        msg="find() with a filter should return matching documents in insertion order",
    ),
]

# Property [Natural Sort Order]: sort({"$natural": 1}) returns documents in
# insertion order (oldest first), sort({"$natural": -1}) returns reverse
# insertion order (most recent first), and limit restricts to the N most recent.
CAPPED_NATURAL_SORT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "forward_insertion_order",
        target_collection=CappedCollection(size=100_000),
        docs=[{"_id": 3}, {"_id": 1}, {"_id": 4}, {"_id": 2}],
        command=lambda ctx: {
            "find": ctx.collection,
            "projection": {"_id": 1},
            "sort": {"$natural": 1},
        },
        expected=[{"_id": 3}, {"_id": 1}, {"_id": 4}, {"_id": 2}],
        msg="$natural: 1 should return documents in insertion order",
    ),
    CommandTestCase(
        "reverse_insertion_order",
        target_collection=CappedCollection(size=100_000),
        docs=[{"_id": 3}, {"_id": 1}, {"_id": 4}, {"_id": 2}],
        command=lambda ctx: {
            "find": ctx.collection,
            "projection": {"_id": 1},
            "sort": {"$natural": -1},
        },
        expected=[{"_id": 2}, {"_id": 4}, {"_id": 1}, {"_id": 3}],
        msg="$natural: -1 should return documents in reverse insertion order",
    ),
    CommandTestCase(
        "reverse_limit_3",
        target_collection=CappedCollection(size=100_000),
        docs=[{"_id": 3}, {"_id": 1}, {"_id": 4}, {"_id": 2}, {"_id": 5}],
        command=lambda ctx: {
            "find": ctx.collection,
            "projection": {"_id": 1},
            "sort": {"$natural": -1},
            "limit": 3,
        },
        expected=[{"_id": 5}, {"_id": 2}, {"_id": 4}],
        msg="$natural: -1 with limit 3 should return the 3 most recent documents",
    ),
]

# Property [Natural Hint Order]: hint({"$natural": 1}) forces forward
# collection scan order, hint({"$natural": -1}) forces reverse.
CAPPED_HINT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "hint_forward_order",
        target_collection=CappedCollection(size=100_000),
        docs=[{"_id": 3}, {"_id": 1}, {"_id": 4}, {"_id": 2}],
        command=lambda ctx: {
            "find": ctx.collection,
            "projection": {"_id": 1},
            "hint": {"$natural": 1},
        },
        expected=[{"_id": 3}, {"_id": 1}, {"_id": 4}, {"_id": 2}],
        msg="hint $natural:1 should return documents in forward insertion order",
    ),
    CommandTestCase(
        "hint_reverse_order",
        target_collection=CappedCollection(size=100_000),
        docs=[{"_id": 3}, {"_id": 1}, {"_id": 4}, {"_id": 2}],
        command=lambda ctx: {
            "find": ctx.collection,
            "projection": {"_id": 1},
            "hint": {"$natural": -1},
        },
        expected=[{"_id": 2}, {"_id": 4}, {"_id": 1}, {"_id": 3}],
        msg="hint $natural:-1 should return documents in reverse insertion order",
    ),
]

# Property [Index Hint Overrides Natural]: hinting a secondary index returns
# documents in index order rather than insertion order.
CAPPED_INDEX_HINT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "index_hint_overrides_natural",
        target_collection=CappedCollection(size=100_000),
        indexes=[IndexModel("x")],
        docs=[{"_id": 1, "x": 30}, {"_id": 2, "x": 10}, {"_id": 3, "x": 20}],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": {"$gte": 10}},
            "hint": "x_1",
            "projection": {"_id": 1},
        },
        expected=[{"_id": 2}, {"_id": 3}, {"_id": 1}],
        msg="Secondary index hint should return documents in index order, not insertion order",
    ),
]

# Property [Aggregate Natural Order]: aggregate on a capped collection preserves
# insertion order unless an explicit $sort or reverse hint is applied.
CAPPED_AGG_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "agg_empty_pipeline",
        target_collection=CappedCollection(size=100_000),
        docs=[{"_id": 3}, {"_id": 1}, {"_id": 4}, {"_id": 2}],
        command=lambda ctx: {"aggregate": ctx.collection, "pipeline": [], "cursor": {}},
        expected=[{"_id": 3}, {"_id": 1}, {"_id": 4}, {"_id": 2}],
        msg="Empty aggregation pipeline should return documents in insertion order",
    ),
    CommandTestCase(
        "agg_hint_natural_forward",
        target_collection=CappedCollection(size=100_000),
        docs=[{"_id": 3}, {"_id": 1}, {"_id": 4}, {"_id": 2}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": {"$natural": 1},
        },
        expected=[{"_id": 3}, {"_id": 1}, {"_id": 4}, {"_id": 2}],
        msg="hint $natural:1 should return documents in insertion order",
    ),
    CommandTestCase(
        "agg_hint_natural_reverse",
        target_collection=CappedCollection(size=100_000),
        docs=[{"_id": 3}, {"_id": 1}, {"_id": 4}, {"_id": 2}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": {"$natural": -1},
        },
        expected=[{"_id": 2}, {"_id": 4}, {"_id": 1}, {"_id": 3}],
        msg="hint $natural:-1 should return documents in reverse insertion order",
    ),
    CommandTestCase(
        "agg_match_preserves_order",
        target_collection=CappedCollection(size=100_000),
        docs=[
            {"_id": 5, "x": "a"},
            {"_id": 2, "x": "b"},
            {"_id": 8, "x": "a"},
            {"_id": 1, "x": "c"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "a"}}, {"$project": {"_id": 1}}],
            "cursor": {},
        },
        expected=[{"_id": 5}, {"_id": 8}],
        msg="Aggregate $match should return matching documents in insertion order",
    ),
]

# Property [Explicit Sort Overrides Natural]: find() with an explicit sort
# field or aggregate $sort overrides the default natural insertion order.
CAPPED_SORT_OVERRIDE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "find_explicit_sort_overrides",
        target_collection=CappedCollection(size=100_000),
        docs=[{"_id": 5}, {"_id": 2}, {"_id": 8}, {"_id": 1}],
        command=lambda ctx: {
            "find": ctx.collection,
            "projection": {"_id": 1},
            "sort": {"_id": 1},
        },
        expected=[{"_id": 1}, {"_id": 2}, {"_id": 5}, {"_id": 8}],
        msg="Explicit sort should override natural insertion order",
    ),
    CommandTestCase(
        "agg_sort_overrides",
        target_collection=CappedCollection(size=100_000),
        docs=[{"_id": 5}, {"_id": 2}, {"_id": 8}, {"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"_id": 1}}, {"$project": {"_id": 1}}],
            "cursor": {},
        },
        expected=[{"_id": 1}, {"_id": 2}, {"_id": 5}, {"_id": 8}],
        msg="Aggregate $sort should override natural insertion order",
    ),
]

CAPPED_SINGLE_COMMAND_TESTS = (
    CAPPED_INSERTION_ORDER_TESTS
    + CAPPED_NATURAL_SORT_TESTS
    + CAPPED_HINT_TESTS
    + CAPPED_INDEX_HINT_TESTS
    + CAPPED_AGG_TESTS
    + CAPPED_SORT_OVERRIDE_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(CAPPED_SINGLE_COMMAND_TESTS))
def test_capped_single_command(database_client, collection, test):
    """Test capped single-command behaviors."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    expected = test.build_expected(ctx)
    assertResult(
        result,
        expected=expected,
        error_code=test.error_code,
        msg=test.msg,
        raw_res=not isinstance(expected, list),
    )


# Property [Batch Boundary Independence]: insertion order is preserved across
# multiple insertMany calls.
@pytest.mark.collection_mgmt
def test_capped_batch_boundaries(database_client, collection):
    """Test insertion order across batch boundaries."""
    coll = CappedCollection(size=100_000).resolve(database_client, collection)
    coll.insert_many([{"_id": 4}, {"_id": 2}])
    coll.insert_many([{"_id": 3}, {"_id": 1}])
    result = execute_command(coll, {"find": coll.name, "projection": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 4}, {"_id": 2}, {"_id": 3}, {"_id": 1}],
        msg="find() should preserve order across multiple insertMany calls",
    )


# Property [Natural Sort Equivalence]: find() without sort produces the same
# order as sort({"$natural": 1}).
@pytest.mark.collection_mgmt
def test_capped_natural_sort_equivalence(database_client, collection):
    """Test that find() without sort equals $natural: 1."""
    coll = CappedCollection(size=100_000).resolve(database_client, collection)
    coll.insert_many([{"_id": 5}, {"_id": 2}, {"_id": 8}, {"_id": 1}])
    unsorted = execute_command(coll, {"find": coll.name, "projection": {"_id": 1}})
    sorted_result = execute_command(
        coll, {"find": coll.name, "projection": {"_id": 1}, "sort": {"$natural": 1}}
    )
    assertSuccess(
        sorted_result,
        unsorted["cursor"]["firstBatch"],
        msg="find() without sort should produce same order as $natural: 1",
    )
