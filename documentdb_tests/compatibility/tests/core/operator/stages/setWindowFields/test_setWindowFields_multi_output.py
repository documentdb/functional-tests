"""
Tests for $setWindowFields multi-output behavior.

These are operator-agnostic — they test the stage's ability to handle
multiple output fields with different accumulators and window specs.

Covers: multiple different operators in one output clause, same operator
with different window specs, multiple operators with different window specs,
and output field that overwrites _id.
"""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command


def test_mixed_operators_multi_output(collection):
    """Multiple different operators ($sum + $avg + $count) in one output clause."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "A", "value": 20},
        {"_id": 3, "partition": "A", "value": 30},
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
                            },
                            "avg": {
                                "$avg": "$value",
                                "window": {"documents": ["unbounded", "unbounded"]},
                            },
                            "cnt": {
                                "$count": {},
                                "window": {"documents": ["unbounded", "unbounded"]},
                            },
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    expected = [
        {"_id": 1, "partition": "A", "value": 10, "total": 60, "avg": 20.0, "cnt": 3},
        {"_id": 2, "partition": "A", "value": 20, "total": 60, "avg": 20.0, "cnt": 3},
        {"_id": 3, "partition": "A", "value": 30, "total": 60, "avg": 20.0, "cnt": 3},
    ]
    assertSuccess(result, expected, msg="mixed operators in one output clause")


def test_same_operator_different_windows(collection):
    """Same operator ($sum) with different window specs in one output clause."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "A", "value": 20},
        {"_id": 3, "partition": "A", "value": 30},
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
                            },
                            "whole": {
                                "$sum": "$value",
                                "window": {"documents": ["unbounded", "unbounded"]},
                            },
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    expected = [
        {"_id": 1, "partition": "A", "value": 10, "cumulative": 10, "whole": 60},
        {"_id": 2, "partition": "A", "value": 20, "cumulative": 30, "whole": 60},
        {"_id": 3, "partition": "A", "value": 30, "cumulative": 60, "whole": 60},
    ]
    assertSuccess(result, expected, msg="same operator with different windows in one output")


def test_output_field_name_id(collection):
    """Output field named '_id' overwrites original document _id."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "A", "value": 20},
        {"_id": 3, "partition": "A", "value": 30},
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
                            "_id": {
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
        {"_id": 60, "partition": "A", "value": 10},
        {"_id": 60, "partition": "A", "value": 20},
        {"_id": 60, "partition": "A", "value": 30},
    ]
    assertSuccess(result, expected, msg="output field _id overwrites document _id")


def test_mixed_operators_different_window_specs(collection):
    """Multiple different operators each with a different window specification."""
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
                            "sum_sliding": {
                                "$sum": "$value",
                                "window": {"documents": [-1, 1]},
                            },
                            "avg_cumulative": {
                                "$avg": "$value",
                                "window": {"documents": ["unbounded", "current"]},
                            },
                            "max_whole": {
                                "$max": "$value",
                                "window": {"documents": ["unbounded", "unbounded"]},
                            },
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    # $sum sliding [-1, 1]: row1=[10,20]=30, row2=[10,20,30]=60, row3=[20,30,40]=90,
    #                        row4=[30,40,50]=120, row5=[40,50]=90
    # $avg cumulative [unbounded, current]: row1=10, row2=15, row3=20, row4=25, row5=30
    # $max whole [unbounded, unbounded]: always 50
    expected = [
        {
            "_id": 1,
            "partition": "A",
            "value": 10,
            "sum_sliding": 30,
            "avg_cumulative": 10.0,
            "max_whole": 50,
        },
        {
            "_id": 2,
            "partition": "A",
            "value": 20,
            "sum_sliding": 60,
            "avg_cumulative": 15.0,
            "max_whole": 50,
        },
        {
            "_id": 3,
            "partition": "A",
            "value": 30,
            "sum_sliding": 90,
            "avg_cumulative": 20.0,
            "max_whole": 50,
        },
        {
            "_id": 4,
            "partition": "A",
            "value": 40,
            "sum_sliding": 120,
            "avg_cumulative": 25.0,
            "max_whole": 50,
        },
        {
            "_id": 5,
            "partition": "A",
            "value": 50,
            "sum_sliding": 90,
            "avg_cumulative": 30.0,
            "max_whole": 50,
        },
    ]
    assertSuccess(
        result,
        expected,
        msg="each operator independently respects its own window spec without cross-contamination",
    )
