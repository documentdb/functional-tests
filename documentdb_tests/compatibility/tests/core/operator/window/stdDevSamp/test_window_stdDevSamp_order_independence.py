"""
Tests for $stdDevSamp order independence in window context.

Verifies that $stdDevSamp produces the same result regardless of sortBy direction,
confirming it is an order-independent operator per TEST_COVERAGE.md §22.
"""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

# Property [Order Independence]: $stdDevSamp produces same result regardless of sort direction


def test_stdDevSamp_whole_partition_ascending_sort(collection):
    """$stdDevSamp whole partition with ascending sort."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "A", "value": 20},
        {"_id": 3, "partition": "A", "value": 30},
        {"_id": 4, "partition": "A", "value": 40},
        {"_id": 5, "partition": "A", "value": 50},
    ]
    collection.insert_many(docs)
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
                                "$stdDevSamp": "$value",
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
        {"_id": 1, "result": 15.811388300841896},
        {"_id": 2, "result": 15.811388300841896},
        {"_id": 3, "result": 15.811388300841896},
        {"_id": 4, "result": 15.811388300841896},
        {"_id": 5, "result": 15.811388300841896},
    ]
    assertSuccess(result, expected, msg="ascending sort produces correct stdDevSamp")


def test_stdDevSamp_whole_partition_descending_sort(collection):
    """$stdDevSamp whole partition with descending sort produces same result as ascending."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "A", "value": 20},
        {"_id": 3, "partition": "A", "value": 30},
        {"_id": 4, "partition": "A", "value": 40},
        {"_id": 5, "partition": "A", "value": 50},
    ]
    collection.insert_many(docs)
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
                                "$stdDevSamp": "$value",
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
        {"_id": 1, "result": 15.811388300841896},
        {"_id": 2, "result": 15.811388300841896},
        {"_id": 3, "result": 15.811388300841896},
        {"_id": 4, "result": 15.811388300841896},
        {"_id": 5, "result": 15.811388300841896},
    ]
    assertSuccess(
        result, expected, msg="descending sort produces same stdDevSamp — order independent"
    )
