"""
Tests for $stdDevPop order independence in window context.

Verifies that $stdDevPop produces the same result regardless of sortBy direction,
confirming it is an order-independent operator per TEST_COVERAGE.md §22.
"""

from documentdb_tests.compatibility.tests.core.operator.window.utils.window_test_case import (
    BASIC_DOCS,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

# Property [Order Independence]: $stdDevPop produces same result regardless of sort direction


def test_stdDevPop_whole_partition_ascending_sort(collection):
    """$stdDevPop whole partition with ascending sort."""
    collection.insert_many(BASIC_DOCS)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": {"_id": 1},
                        "output": {
                            "result": {
                                "$stdDevPop": "$value",
                                "window": {"documents": ["unbounded", "unbounded"]},
                            }
                        },
                    }
                },
                {"$sort": {"_id": 1}},
                {"$project": {"_id": 1, "result": 1}},
            ],
            "cursor": {},
        },
    )
    expected = [
        {"_id": 1, "result": 14.142135623730951},
        {"_id": 2, "result": 14.142135623730951},
        {"_id": 3, "result": 14.142135623730951},
        {"_id": 4, "result": 14.142135623730951},
        {"_id": 5, "result": 14.142135623730951},
    ]
    assertSuccess(result, expected, msg="ascending sort produces correct stdDevPop")


def test_stdDevPop_whole_partition_descending_sort(collection):
    """$stdDevPop whole partition with descending sort produces same result as ascending."""
    collection.insert_many(BASIC_DOCS)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": {"_id": -1},
                        "output": {
                            "result": {
                                "$stdDevPop": "$value",
                                "window": {"documents": ["unbounded", "unbounded"]},
                            }
                        },
                    }
                },
                {"$sort": {"_id": 1}},
                {"$project": {"_id": 1, "result": 1}},
            ],
            "cursor": {},
        },
    )
    # Same result regardless of sort direction — order-independent operator
    expected = [
        {"_id": 1, "result": 14.142135623730951},
        {"_id": 2, "result": 14.142135623730951},
        {"_id": 3, "result": 14.142135623730951},
        {"_id": 4, "result": 14.142135623730951},
        {"_id": 5, "result": 14.142135623730951},
    ]
    assertSuccess(
        result, expected, msg="descending sort produces same stdDevPop — order independent"
    )
