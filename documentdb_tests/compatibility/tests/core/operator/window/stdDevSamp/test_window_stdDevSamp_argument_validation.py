"""
Tests for $stdDevSamp argument validation in window context.

Covers: invalid expression types, empty object as expression,
array with multiple expressions (invalid for window form),
and non-expression argument types.
"""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

# Property [Valid Expression Forms]: accepted expression inputs


def test_stdDevSamp_field_path_expression(collection):
    """$stdDevSamp accepts a field path expression."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "A", "value": 20},
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
                }
            ],
            "cursor": {},
        },
    )
    expected = [
        {"_id": 1, "partition": "A", "value": 10, "result": 7.0710678118654755},
        {"_id": 2, "partition": "A", "value": 20, "result": 7.0710678118654755},
    ]
    assertSuccess(result, expected, msg="field path expression accepted")


def test_stdDevSamp_operator_expression(collection):
    """$stdDevSamp accepts an operator expression."""
    docs = [
        {"_id": 1, "partition": "A", "value": 5},
        {"_id": 2, "partition": "A", "value": 10},
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
                                "$stdDevSamp": {"$multiply": ["$value", 2]},
                                "window": {"documents": ["unbounded", "unbounded"]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    # Values: [10, 20] -> stdDevSamp = sqrt(50) = 7.071
    expected = [
        {"_id": 1, "partition": "A", "value": 5, "result": 7.0710678118654755},
        {"_id": 2, "partition": "A", "value": 10, "result": 7.0710678118654755},
    ]
    assertSuccess(result, expected, msg="operator expression accepted")


def test_stdDevSamp_literal_numeric_expression(collection):
    """$stdDevSamp with a literal numeric value — all rows get same value, stddev is 0."""
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
                            "result": {
                                "$stdDevSamp": {"$literal": 42},
                                "window": {"documents": ["unbounded", "unbounded"]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    # All rows evaluate to 42 -> stdDevSamp = 0
    expected = [
        {"_id": 1, "partition": "A", "value": 10, "result": 0.0},
        {"_id": 2, "partition": "A", "value": 20, "result": 0.0},
        {"_id": 3, "partition": "A", "value": 30, "result": 0.0},
    ]
    assertSuccess(result, expected, msg="literal numeric expression produces 0 stddev")


# Property [Invalid Argument Shapes]: rejected input forms


def test_stdDevSamp_empty_string_expression(collection):
    """$stdDevSamp with empty string (not a valid field path) — treated as non-numeric."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "A", "value": 20},
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
                                "$stdDevSamp": "",
                                "window": {"documents": ["unbounded", "unbounded"]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    # Empty string is a literal string constant, non-numeric -> all null
    expected = [
        {"_id": 1, "partition": "A", "value": 10, "result": None},
        {"_id": 2, "partition": "A", "value": 20, "result": None},
    ]
    assertSuccess(result, expected, msg="empty string treated as non-numeric constant")


def test_stdDevSamp_array_multiple_expressions_rejected(collection):
    """$stdDevSamp with array of multiple field paths in window context returns null."""
    docs = [
        {"_id": 1, "partition": "A", "x": 10, "y": 20},
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
                                "$stdDevSamp": ["$x", "$y"],
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
        {"_id": 1, "partition": "A", "x": 10, "y": 20, "result": None},
    ]
    assertSuccess(result, expected, msg="array of multiple expressions returns null in window form")
