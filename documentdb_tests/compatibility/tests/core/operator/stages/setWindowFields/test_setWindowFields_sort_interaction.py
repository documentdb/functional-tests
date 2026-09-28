"""
Tests for $setWindowFields sort interaction behavior.

Using $sum as a sample operator, verifies that the stage respects the specified
sort order and that changing sort order produces correspondingly different
results for order-dependent window computations.

Covers: ascending vs descending sort with cumulative frames, compound sort,
sort with ties and tiebreaker, and sort on non-_id field.

Note: These stage-level tests verify the stage's sort mechanics.
Per-operator tests verify operator-specific sort interactions.
"""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

# Property [Ascending vs Descending]: sort direction changes cumulative frame results


def test_ascending_sort_cumulative(collection):
    """Ascending sort with cumulative window accumulates in _id order."""
    docs = [
        {"_id": 1, "partition": "A", "value": 1},
        {"_id": 2, "partition": "A", "value": 2},
        {"_id": 3, "partition": "A", "value": 4},
        {"_id": 4, "partition": "A", "value": 8},
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
                                "window": {"documents": ["unbounded", "current"]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    expected = [
        {"_id": 1, "partition": "A", "value": 1, "result": 1},
        {"_id": 2, "partition": "A", "value": 2, "result": 3},
        {"_id": 3, "partition": "A", "value": 4, "result": 7},
        {"_id": 4, "partition": "A", "value": 8, "result": 15},
    ]
    assertSuccess(result, expected, msg="ascending sort cumulative [unbounded, current]")


def test_descending_sort_cumulative(collection):
    """Descending sort with cumulative window accumulates in reverse _id order."""
    docs = [
        {"_id": 1, "partition": "A", "value": 1},
        {"_id": 2, "partition": "A", "value": 2},
        {"_id": 3, "partition": "A", "value": 4},
        {"_id": 4, "partition": "A", "value": 8},
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
                                "$sum": "$value",
                                "window": {"documents": ["unbounded", "current"]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    # Descending: id=4, 3, 2, 1 -> cumulative: 8, 12, 14, 15
    expected = [
        {"_id": 4, "partition": "A", "value": 8, "result": 8},
        {"_id": 3, "partition": "A", "value": 4, "result": 12},
        {"_id": 2, "partition": "A", "value": 2, "result": 14},
        {"_id": 1, "partition": "A", "value": 1, "result": 15},
    ]
    assertSuccess(result, expected, msg="descending sort cumulative [unbounded, current]")


# Property [Compound Sort]: multi-key sort determines row ordering


def test_compound_sort(collection):
    """Compound sort {a: 1, b: -1} correctly determines row ordering."""
    docs = [
        {"_id": 1, "partition": "A", "a": 1, "b": 2, "value": 1},
        {"_id": 2, "partition": "A", "a": 1, "b": 1, "value": 2},
        {"_id": 3, "partition": "A", "a": 2, "b": 2, "value": 4},
        {"_id": 4, "partition": "A", "a": 2, "b": 1, "value": 8},
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
                        "sortBy": {"a": 1, "b": -1},
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": {"documents": ["unbounded", "current"]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    # Sort: a=1,b=2(id=1) -> a=1,b=1(id=2) -> a=2,b=2(id=3) -> a=2,b=1(id=4)
    # Cumulative: 1, 3, 7, 15
    expected = [
        {"_id": 1, "partition": "A", "a": 1, "b": 2, "value": 1, "result": 1},
        {"_id": 2, "partition": "A", "a": 1, "b": 1, "value": 2, "result": 3},
        {"_id": 3, "partition": "A", "a": 2, "b": 2, "value": 4, "result": 7},
        {"_id": 4, "partition": "A", "a": 2, "b": 1, "value": 8, "result": 15},
    ]
    assertSuccess(result, expected, msg="compound sort {a:1, b:-1} determines ordering")


# Property [Sort on Non-_id Field]: sortBy on arbitrary field


def test_sort_on_non_id_field(collection):
    """SortBy on a non-_id field correctly determines row ordering."""
    docs = [
        {"_id": 3, "partition": "A", "ts": 100, "value": 4},
        {"_id": 1, "partition": "A", "ts": 200, "value": 1},
        {"_id": 2, "partition": "A", "ts": 300, "value": 2},
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
                        "sortBy": {"ts": 1},
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": {"documents": ["unbounded", "current"]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    # Sort by ts: id=3(ts=100), id=1(ts=200), id=2(ts=300)
    # Cumulative: 4, 5, 7
    expected = [
        {"_id": 3, "partition": "A", "ts": 100, "value": 4, "result": 4},
        {"_id": 1, "partition": "A", "ts": 200, "value": 1, "result": 5},
        {"_id": 2, "partition": "A", "ts": 300, "value": 2, "result": 7},
    ]
    assertSuccess(result, expected, msg="sortBy on non-_id field (ts)")


# Property [Sort With Ties]: tied sortBy values with compound tiebreaker


def test_sort_with_ties_and_tiebreaker(collection):
    """Ties in sortBy resolved by compound sort tiebreaker."""
    docs = [
        {"_id": 1, "partition": "A", "score": 10, "value": 1},
        {"_id": 2, "partition": "A", "score": 10, "value": 2},
        {"_id": 3, "partition": "A", "score": 10, "value": 4},
        {"_id": 4, "partition": "A", "score": 20, "value": 8},
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
                        "sortBy": {"score": 1, "_id": 1},
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": {"documents": [-1, 0]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    # Sort: score=10,id=1 -> score=10,id=2 -> score=10,id=3 -> score=20,id=4
    # Trailing [-1, 0]:
    # Row 1: [1] = 1
    # Row 2: [1, 2] = 3
    # Row 3: [2, 4] = 6
    # Row 4: [4, 8] = 12
    expected = [
        {"_id": 1, "partition": "A", "score": 10, "value": 1, "result": 1},
        {"_id": 2, "partition": "A", "score": 10, "value": 2, "result": 3},
        {"_id": 3, "partition": "A", "score": 10, "value": 4, "result": 6},
        {"_id": 4, "partition": "A", "score": 20, "value": 8, "result": 12},
    ]
    assertSuccess(result, expected, msg="ties resolved by compound sort tiebreaker")
