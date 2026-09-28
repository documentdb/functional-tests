"""
Tests for $setWindowFields pipeline stage composition.

Using $sum as a sample operator, verifies that the stage composes correctly
with preceding and following pipeline stages.

Covers: $match before, $project after, $sort before, $limit before,
$unwind before, $group before, and chained $setWindowFields.

Note: These stage-level tests verify the stage's composability.
Per-operator tests verify operator-specific pipeline interactions.
"""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

# Property [Match Before]: $match restricts input to $setWindowFields


def test_match_before_window(collection):
    """$match before $setWindowFields restricts the input documents."""
    docs = [
        {"_id": 1, "partition": "A", "active": True, "value": 1},
        {"_id": 2, "partition": "A", "active": False, "value": 2},
        {"_id": 3, "partition": "A", "active": True, "value": 4},
        {"_id": 4, "partition": "A", "active": True, "value": 8},
    ]
    collection.insert_many(docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$match": {"active": True}},
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
                },
            ],
            "cursor": {},
        },
    )
    # Only active=True docs: values 1, 4, 8 -> sum = 13
    expected = [
        {"_id": 1, "partition": "A", "active": True, "value": 1, "result": 13},
        {"_id": 3, "partition": "A", "active": True, "value": 4, "result": 13},
        {"_id": 4, "partition": "A", "active": True, "value": 8, "result": 13},
    ]
    assertSuccess(result, expected, msg="$match before restricts window input")


# Property [Project After]: $project after $setWindowFields reshapes output


def test_project_after_window(collection):
    """$project after $setWindowFields reshapes the output."""
    docs = [
        {"_id": 1, "partition": "A", "value": 1},
        {"_id": 2, "partition": "A", "value": 2},
        {"_id": 3, "partition": "A", "value": 4},
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
                            "total": {
                                "$sum": "$value",
                                "window": {"documents": ["unbounded", "unbounded"]},
                            }
                        },
                    }
                },
                {"$project": {"_id": 1, "total": 1}},
            ],
            "cursor": {},
        },
    )
    expected = [
        {"_id": 1, "total": 7},
        {"_id": 2, "total": 7},
        {"_id": 3, "total": 7},
    ]
    assertSuccess(result, expected, msg="$project after reshapes window output")


# Property [Limit Before]: $limit restricts input to $setWindowFields


def test_limit_before_window(collection):
    """$limit before $setWindowFields restricts the input set."""
    docs = [
        {"_id": 1, "partition": "A", "value": 1},
        {"_id": 2, "partition": "A", "value": 2},
        {"_id": 3, "partition": "A", "value": 4},
        {"_id": 4, "partition": "A", "value": 8},
        {"_id": 5, "partition": "A", "value": 16},
    ]
    collection.insert_many(docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$sort": {"_id": 1}},
                {"$limit": 3},
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
                },
            ],
            "cursor": {},
        },
    )
    # After limit: 3 docs with values 1, 2, 4 -> sum = 7
    expected = [
        {"_id": 1, "partition": "A", "value": 1, "result": 7},
        {"_id": 2, "partition": "A", "value": 2, "result": 7},
        {"_id": 3, "partition": "A", "value": 4, "result": 7},
    ]
    assertSuccess(result, expected, msg="$limit before restricts window input")


# Property [Match After]: $match can filter on computed window fields


def test_match_after_window(collection):
    """$match after $setWindowFields filters on computed field."""
    docs = [
        {"_id": 1, "partition": "A", "value": 1},
        {"_id": 2, "partition": "A", "value": 2},
        {"_id": 3, "partition": "A", "value": 4},
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
                            "cumulative": {
                                "$sum": "$value",
                                "window": {"documents": ["unbounded", "current"]},
                            }
                        },
                    }
                },
                {"$match": {"cumulative": {"$gte": 3}}},
            ],
            "cursor": {},
        },
    )
    # Cumulative: 1, 3, 7 -> filter >= 3 keeps id=2, id=3
    expected = [
        {"_id": 2, "partition": "A", "value": 2, "cumulative": 3},
        {"_id": 3, "partition": "A", "value": 4, "cumulative": 7},
    ]
    assertSuccess(result, expected, msg="$match after filters on computed window field")


# Property [Chained Window Stages]: multiple $setWindowFields stages in sequence


def test_chained_window_stages(collection):
    """Chained $setWindowFields — second stage uses output of first."""
    docs = [
        {"_id": 1, "partition": "A", "value": 1},
        {"_id": 2, "partition": "A", "value": 2},
        {"_id": 3, "partition": "A", "value": 4},
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
                            "cumulative": {
                                "$sum": "$value",
                                "window": {"documents": ["unbounded", "current"]},
                            }
                        },
                    }
                },
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": {"_id": 1},
                        "output": {
                            "totalOfCumulative": {
                                "$sum": "$cumulative",
                                "window": {"documents": ["unbounded", "unbounded"]},
                            }
                        },
                    }
                },
            ],
            "cursor": {},
        },
    )
    # cumulative: 1, 3, 7
    # totalOfCumulative: 1+3+7 = 11
    expected = [
        {"_id": 1, "partition": "A", "value": 1, "cumulative": 1, "totalOfCumulative": 11},
        {"_id": 2, "partition": "A", "value": 2, "cumulative": 3, "totalOfCumulative": 11},
        {"_id": 3, "partition": "A", "value": 4, "cumulative": 7, "totalOfCumulative": 11},
    ]
    assertSuccess(result, expected, msg="chained $setWindowFields stages compose correctly")


# Property [Unwind Before]: $unwind produces multiple docs fed into window


def test_unwind_before_window(collection):
    """$unwind before $setWindowFields — window operates on unwound documents."""
    docs = [
        {"_id": 1, "partition": "A", "values": [1, 2, 4]},
        {"_id": 2, "partition": "A", "values": [8, 16]},
    ]
    collection.insert_many(docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$unwind": "$values"},
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": {"values": 1},
                        "output": {
                            "result": {
                                "$sum": "$values",
                                "window": {"documents": ["unbounded", "unbounded"]},
                            }
                        },
                    }
                },
                {"$sort": {"values": 1}},
            ],
            "cursor": {},
        },
    )
    # After unwind: 5 docs with values 1, 2, 4, 8, 16 -> sum = 31
    expected = [
        {"_id": 1, "partition": "A", "values": 1, "result": 31},
        {"_id": 1, "partition": "A", "values": 2, "result": 31},
        {"_id": 1, "partition": "A", "values": 4, "result": 31},
        {"_id": 2, "partition": "A", "values": 8, "result": 31},
        {"_id": 2, "partition": "A", "values": 16, "result": 31},
    ]
    assertSuccess(result, expected, msg="$unwind before — window operates on unwound docs")
