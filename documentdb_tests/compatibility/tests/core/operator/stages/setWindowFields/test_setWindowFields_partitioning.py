"""
Tests for $setWindowFields partitioning behavior.

Using $sum as a sample operator, verifies that the stage correctly isolates
computation within each partition when data spans multiple partitions.

Covers: partition isolation, no partitionBy (whole collection), expression-based
partitioning, null/missing partition keys.

Note: These stage-level tests verify the stage's partitioning mechanics.
Per-operator tests verify operator computation given a partition's documents.
"""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

# Property [Partition Isolation]: frames never cross partition boundaries


def test_partition_isolation(collection):
    """$sum frame never crosses partition boundary."""
    docs = [
        {"_id": 1, "partition": "A", "value": 1},
        {"_id": 2, "partition": "A", "value": 2},
        {"_id": 3, "partition": "A", "value": 4},
        {"_id": 4, "partition": "B", "value": 10},
        {"_id": 5, "partition": "B", "value": 20},
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
                                "$sum": "$value",
                                "window": {"documents": ["unbounded", "unbounded"]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    expected = [
        {"_id": 1, "partition": "A", "value": 1, "result": 7},
        {"_id": 2, "partition": "A", "value": 2, "result": 7},
        {"_id": 3, "partition": "A", "value": 4, "result": 7},
        {"_id": 4, "partition": "B", "value": 10, "result": 30},
        {"_id": 5, "partition": "B", "value": 20, "result": 30},
    ]
    assertSuccess(result, expected, msg="partitions A and B compute independently")


def test_sliding_window_respects_partition_boundary(collection):
    """Sliding window at partition edge does not include docs from other partition."""
    docs = [
        {"_id": 1, "partition": "A", "value": 1},
        {"_id": 2, "partition": "A", "value": 2},
        {"_id": 3, "partition": "B", "value": 100},
        {"_id": 4, "partition": "B", "value": 200},
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
                                "$sum": "$value",
                                "window": {"documents": [-1, 1]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    # A: id=1 [1,2]=3; id=2 [1,2]=3
    # B: id=3 [100,200]=300; id=4 [100,200]=300
    expected = [
        {"_id": 1, "partition": "A", "value": 1, "result": 3},
        {"_id": 2, "partition": "A", "value": 2, "result": 3},
        {"_id": 3, "partition": "B", "value": 100, "result": 300},
        {"_id": 4, "partition": "B", "value": 200, "result": 300},
    ]
    assertSuccess(result, expected, msg="sliding window does not cross partition boundary")


# Property [No PartitionBy]: entire collection treated as one partition


def test_no_partition_by(collection):
    """Omitting partitionBy treats entire collection as one partition."""
    docs = [
        {"_id": 1, "group": "A", "value": 1},
        {"_id": 2, "group": "B", "value": 2},
        {"_id": 3, "group": "A", "value": 4},
    ]
    collection.insert_many(docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "sortBy": {"_id": 1},
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": {"documents": ["unbounded", "unbounded"]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    expected = [
        {"_id": 1, "group": "A", "value": 1, "result": 7},
        {"_id": 2, "group": "B", "value": 2, "result": 7},
        {"_id": 3, "group": "A", "value": 4, "result": 7},
    ]
    assertSuccess(result, expected, msg="no partitionBy — whole collection is one partition")


# Property [Null Partition Key]: null and missing partition keys group together


def test_null_partition_key(collection):
    """Documents with null partition key group into one partition."""
    docs = [
        {"_id": 1, "partition": None, "value": 1},
        {"_id": 2, "partition": None, "value": 2},
        {"_id": 3, "partition": "A", "value": 10},
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
                                "$sum": "$value",
                                "window": {"documents": ["unbounded", "unbounded"]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    expected = [
        {"_id": 1, "partition": None, "value": 1, "result": 3},
        {"_id": 2, "partition": None, "value": 2, "result": 3},
        {"_id": 3, "partition": "A", "value": 10, "result": 10},
    ]
    assertSuccess(result, expected, msg="null partition keys group together")


def test_missing_partition_key(collection):
    """Documents with missing partition key group into one partition (same as null)."""
    docs = [
        {"_id": 1, "value": 1},
        {"_id": 2, "value": 2},
        {"_id": 3, "partition": "A", "value": 10},
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
                                "$sum": "$value",
                                "window": {"documents": ["unbounded", "unbounded"]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    expected = [
        {"_id": 1, "value": 1, "result": 3},
        {"_id": 2, "value": 2, "result": 3},
        {"_id": 3, "partition": "A", "value": 10, "result": 10},
    ]
    assertSuccess(result, expected, msg="missing partition key groups into null partition")


# Property [Expression PartitionBy]: expression-based partition key


def test_expression_partition_by(collection):
    """Expression-based partitionBy groups documents correctly."""
    docs = [
        {"_id": 1, "category": "food", "sub": "fruit", "value": 1},
        {"_id": 2, "category": "food", "sub": "meat", "value": 2},
        {"_id": 3, "category": "drink", "sub": "water", "value": 4},
        {"_id": 4, "category": "drink", "sub": "juice", "value": 8},
    ]
    collection.insert_many(docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$category",
                        "sortBy": {"_id": 1},
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": {"documents": ["unbounded", "unbounded"]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    expected = [
        {"_id": 3, "category": "drink", "sub": "water", "value": 4, "result": 12},
        {"_id": 4, "category": "drink", "sub": "juice", "value": 8, "result": 12},
        {"_id": 1, "category": "food", "sub": "fruit", "value": 1, "result": 3},
        {"_id": 2, "category": "food", "sub": "meat", "value": 2, "result": 3},
    ]
    assertSuccess(
        result, expected, ignore_doc_order=True, msg="expression partitionBy groups correctly"
    )
