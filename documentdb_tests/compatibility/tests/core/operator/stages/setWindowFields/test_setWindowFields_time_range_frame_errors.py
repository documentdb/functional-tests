"""
Tests for $setWindowFields time-range mode frame validation errors.

These are operator-agnostic — frame spec validation happens before the
accumulator runs. Uses $sum as the simplest accumulator.

Covers: invalid time unit string, time unit with non-date sortBy value,
boolean bounds with unit, null bounds with unit, lower > upper with unit.
"""

from datetime import datetime, timezone

from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import FAILED_TO_PARSE_ERROR
from documentdb_tests.framework.executor import execute_command

# Property [Time Unit Validation]: time unit must be a valid string


def test_time_range_invalid_unit(collection):
    """Range with invalid time unit produces error."""
    docs = [
        {"_id": 1, "partition": "A", "date": datetime(2023, 1, 1, tzinfo=timezone.utc), "value": 10}
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
                        "sortBy": {"date": 1},
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": {"range": [-1, 0], "unit": "invalid_unit"},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, FAILED_TO_PARSE_ERROR, msg="invalid time unit rejected")


# Property [Date SortBy Requirement]: time unit requires date-type sortBy value


def test_time_range_unit_without_date_sortby(collection):
    """Range with time unit but non-date sortBy value produces error."""
    docs = [{"_id": 1, "partition": "A", "score": 10, "value": 10}]
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
                                "window": {"range": [-1, 0], "unit": "day"},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, 5429513, msg="time unit with non-date sortBy rejected")


# Property [Bound Type Validation with Unit]: bounds must be numeric when unit is specified


def test_time_range_boolean_bound_with_unit(collection):
    """Boolean bound with time unit produces error."""
    docs = [
        {"_id": 1, "partition": "A", "date": datetime(2023, 1, 1, tzinfo=timezone.utc), "value": 10}
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
                        "sortBy": {"date": 1},
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": {"range": [True, 1], "unit": "day"},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, FAILED_TO_PARSE_ERROR, msg="boolean bound with time unit rejected")


def test_time_range_null_bound_with_unit(collection):
    """Null bound with time unit produces error."""
    docs = [
        {"_id": 1, "partition": "A", "date": datetime(2023, 1, 1, tzinfo=timezone.utc), "value": 10}
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
                        "sortBy": {"date": 1},
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": {"range": [None, 1], "unit": "day"},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, FAILED_TO_PARSE_ERROR, msg="null bound with time unit rejected")


# Property [Bound Ordering with Unit]: lower bound must not exceed upper bound


def test_time_range_lower_exceeds_upper_with_unit(collection):
    """Time-range bounds with lower > upper produces error."""
    docs = [
        {"_id": 1, "partition": "A", "date": datetime(2023, 1, 1, tzinfo=timezone.utc), "value": 10}
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
                        "sortBy": {"date": 1},
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": {"range": [5, -5], "unit": "day"},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, 5339900, msg="lower > upper with time unit rejected")
