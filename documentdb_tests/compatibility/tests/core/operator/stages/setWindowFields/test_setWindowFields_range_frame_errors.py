"""
Tests for $setWindowFields range-mode window frame validation errors.

These are operator-agnostic — frame spec validation happens before the
accumulator runs. Uses $sum as the simplest accumulator.

Covers: invalid bound types (non-numeric string, boolean, null), wrong-length
bounds arrays, null/missing sortBy values, no sortBy, descending sort,
multiple sortBy fields, lower > upper, and non-numeric sortBy values.
"""

from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import FAILED_TO_PARSE_ERROR
from documentdb_tests.framework.executor import execute_command

# Property [Range Bound Validation]: range bounds must be numeric or keyword


def test_range_non_numeric_bound(collection):
    """Range bound that is non-numeric (string, not 'unbounded'/'current') produces error."""
    docs = [{"_id": 1, "partition": "A", "score": 1, "value": 10}]
    collection.insert_many(docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": {"score": 1},
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": {"range": ["invalid", 0]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(
        result, FAILED_TO_PARSE_ERROR, msg="non-numeric, non-keyword range bound rejected"
    )


def test_range_boolean_bound(collection):
    """Range bound that is a boolean produces error."""
    docs = [{"_id": 1, "partition": "A", "score": 1, "value": 10}]
    collection.insert_many(docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": {"score": 1},
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": {"range": [True, 10]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, FAILED_TO_PARSE_ERROR, msg="boolean range bound rejected")


def test_range_null_bound(collection):
    """Range bound that is null produces error."""
    docs = [{"_id": 1, "partition": "A", "score": 1, "value": 10}]
    collection.insert_many(docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": {"score": 1},
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": {"range": [None, 10]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, FAILED_TO_PARSE_ERROR, msg="null range bound rejected")


def test_range_empty_bounds_array(collection):
    """Range with empty bounds array produces error."""
    docs = [{"_id": 1, "partition": "A", "score": 1, "value": 10}]
    collection.insert_many(docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": {"score": 1},
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": {"range": []},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, FAILED_TO_PARSE_ERROR, msg="empty range bounds array rejected")


def test_range_three_element_bounds(collection):
    """Range with three-element bounds array produces error."""
    docs = [{"_id": 1, "partition": "A", "score": 1, "value": 10}]
    collection.insert_many(docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": {"score": 1},
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": {"range": [-10, 0, 10]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, FAILED_TO_PARSE_ERROR, msg="three-element range bounds rejected")


# Property [SortBy Value Validation]: sortBy field values must be numeric


def test_range_null_sortby_value(collection):
    """Range mode with null sortBy value produces error 5429414."""
    docs = [
        {"_id": 1, "partition": "A", "score": None, "value": 10},
        {"_id": 2, "partition": "A", "score": 5, "value": 20},
        {"_id": 3, "partition": "A", "score": 10, "value": 30},
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
                        "sortBy": {"score": 1},
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": {"range": [-10, 10]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, 5429414, msg="null sortBy value in range mode rejected")


def test_range_missing_sortby_field(collection):
    """Range mode with missing sortBy field produces error 5429414."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "A", "score": 5, "value": 20},
        {"_id": 3, "partition": "A", "score": 10, "value": 30},
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
                        "sortBy": {"score": 1},
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": {"range": [-10, 10]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, 5429414, msg="missing sortBy field in range mode rejected")


def test_range_non_numeric_sortby_value(collection):
    """Range mode with non-numeric sortBy value produces error 5429414."""
    docs = [
        {"_id": 1, "partition": "A", "score": "abc", "value": 10},
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
                        "sortBy": {"score": 1},
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": {"range": [-10, 10]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, 5429414, msg="non-numeric sortBy value rejected in range mode")


# Property [SortBy Requirement]: range mode requires single ascending sortBy


def test_range_no_sortby(collection):
    """Range window without sortBy produces error."""
    docs = [{"_id": 1, "partition": "A", "value": 10}]
    collection.insert_many(docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": {"range": [-10, 10]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, 5339902, msg="range window without sortBy rejected")


def test_range_descending_sort(collection):
    """Range mode with descending sort produces error 8947401."""
    docs = [{"_id": 1, "partition": "A", "score": 1, "value": 10}]
    collection.insert_many(docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": {"score": -1},
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": {"range": [-10, 10]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, 8947401, msg="descending sort rejected in range mode")


def test_range_multiple_sortby(collection):
    """Range mode with multiple sortBy fields produces error 5339902."""
    docs = [{"_id": 1, "partition": "A", "score": 1, "value": 10}]
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
                                "window": {"range": [-10, 10]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, 5339902, msg="multiple sortBy rejected in range mode")


# Property [Bound Ordering]: lower bound must not exceed upper bound


def test_range_lower_exceeds_upper(collection):
    """Range bounds with lower > upper produces error 5339900."""
    docs = [{"_id": 1, "partition": "A", "score": 1, "value": 10}]
    collection.insert_many(docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": {"score": 1},
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": {"range": [10, -10]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, 5339900, msg="lower > upper rejected in range mode")
