"""Tests for planCacheClear command behavioral verification.

Verifies that planCacheClear actually clears plan cache entries, not just
that it returns ok: 1.0. Uses $planCacheStats to observe cache state before
and after clearing.
"""

from __future__ import annotations

from pymongo.collection import Collection
from pymongo.operations import IndexModel

from documentdb_tests.framework.assertions import assertNotError, assertResult, assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Gte


def _setup_and_warm(collection: Collection, min_entries: int = 1) -> None:
    """Insert docs, create competing indexes, and warm the plan cache.

    Raises AssertionError if the plan cache does not reach *min_entries*
    after warming.
    """
    collection.insert_many([{"_id": i, "a": i, "b": i % 5, "c": i % 3} for i in range(200)])
    collection.create_indexes(
        [
            IndexModel([("a", 1)]),
            IndexModel([("b", 1)]),
            IndexModel([("c", 1)]),
            IndexModel([("a", 1), ("b", 1)]),
            IndexModel([("b", 1), ("c", 1)]),
        ]
    )
    for _ in range(5):
        list(collection.find({"a": 5, "b": 2}))
        list(collection.find({"b": 2, "c": 1}))
        list(collection.find({"a": {"$gt": 3}, "b": 2, "c": 1}))

    count_result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$planCacheStats": {}}, {"$count": "total"}],
            "cursor": {},
        },
    )
    assertNotError(count_result, msg="$planCacheStats precondition check")
    docs = count_result.get("cursor", {}).get("firstBatch", [])
    total = docs[0].get("total", 0) if docs else 0
    if total < min_entries:
        raise AssertionError(
            f"Precondition failed: expected at least {min_entries} plan cache "
            f"entries after warming, got {total}"
        )


# Property [Clear All]: planCacheClear without query shape parameters removes
# all plan cache entries for the collection.
def test_planCacheClear_clears_all_entries(collection: Collection):
    """Test planCacheClear removes all plan cache entries."""
    _setup_and_warm(collection, min_entries=1)

    execute_command(collection, {"planCacheClear": collection.name})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$planCacheStats": {}}, {"$count": "total"}],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [],
        msg="Plan cache should be empty after planCacheClear",
    )


# Property [Targeted Clear]: planCacheClear with a query shape removes the
# matching entry but leaves other entries intact.
def test_planCacheClear_targeted_preserves_other_shapes(collection: Collection):
    """Test planCacheClear with query shape leaves non-targeted entries."""
    _setup_and_warm(collection, min_entries=2)

    execute_command(
        collection,
        {"planCacheClear": collection.name, "query": {"a": 5, "b": 2}},
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$planCacheStats": {}}, {"$count": "total"}],
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected={"total": Gte(1)},
        msg="Plan cache should still have entries for non-targeted shapes after targeted clear",
    )
