"""
Tests for $addToSet order independence in window context.

Verifies $addToSet yields the same whole-partition set regardless of sortBy
direction. Uses distinct values (no cross-type numeric equivalence, whose kept
representation depends on sort order). Results compared with ignore_order_in=["result"].
"""

from documentdb_tests.compatibility.tests.core.operator.window.utils.window_test_case import (
    BASIC_DOCS,
    run_window_operator,
)
from documentdb_tests.framework.assertions import assertSuccess

WHOLE = {"documents": ["unbounded", "unbounded"]}
PROJECT_RESULT = [{"$sort": {"_id": 1}}, {"$project": {"_id": 1, "result": 1}}]

# Property [Order Independence]: $addToSet yields the same whole-partition set for any sort order.


def test_addToSet_whole_partition_ascending_sort(collection):
    """$addToSet whole partition with ascending sort produces the full set."""
    result = run_window_operator(
        collection,
        "$addToSet",
        BASIC_DOCS,
        WHOLE,
        sort_by={"_id": 1},
        extra_stages=PROJECT_RESULT,
    )
    expected = [
        {"_id": 1, "result": [10, 20, 30, 40, 50]},
        {"_id": 2, "result": [10, 20, 30, 40, 50]},
        {"_id": 3, "result": [10, 20, 30, 40, 50]},
        {"_id": 4, "result": [10, 20, 30, 40, 50]},
        {"_id": 5, "result": [10, 20, 30, 40, 50]},
    ]
    assertSuccess(
        result, expected, msg="ascending sort produces the full set", ignore_order_in=["result"]
    )


def test_addToSet_whole_partition_descending_sort(collection):
    """$addToSet whole partition with descending sort produces the same set as ascending."""
    result = run_window_operator(
        collection,
        "$addToSet",
        BASIC_DOCS,
        WHOLE,
        sort_by={"_id": -1},
        extra_stages=PROJECT_RESULT,
    )
    # Same set regardless of sort direction — order-independent operator.
    expected = [
        {"_id": 1, "result": [10, 20, 30, 40, 50]},
        {"_id": 2, "result": [10, 20, 30, 40, 50]},
        {"_id": 3, "result": [10, 20, 30, 40, 50]},
        {"_id": 4, "result": [10, 20, 30, 40, 50]},
        {"_id": 5, "result": [10, 20, 30, 40, 50]},
    ]
    assertSuccess(
        result,
        expected,
        msg="descending sort produces the same set — order independent",
        ignore_order_in=["result"],
    )
