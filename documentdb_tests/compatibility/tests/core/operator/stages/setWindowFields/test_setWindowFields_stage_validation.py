"""
Tests for $setWindowFields stage-level validation errors not covered elsewhere.

Covers: output = empty document {}, sortBy non-object types, sortBy empty object,
sortBy with invalid direction values, window = empty document {}, and
window = scalar (integer).
"""

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import (
    FAILED_TO_PARSE_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command

SINGLE_DOC = [{"_id": 1, "partition": "A", "value": 10}]

# Property [Output Empty Document]: output = {} is valid (no output fields computed)


def test_output_empty_document(collection):
    """$setWindowFields with output: {} (empty document) succeeds — no output fields added."""
    collection.insert_many(SINGLE_DOC)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": {"_id": 1},
                        "output": {},
                    }
                }
            ],
            "cursor": {},
        },
    )
    expected = [{"_id": 1, "partition": "A", "value": 10}]
    assertSuccess(result, expected, msg="output: {} succeeds with no output fields added")


# Property [SortBy Type Validation]: sortBy must be a document


def test_sortby_integer(collection):
    """$setWindowFields with sortBy: 5 (integer) produces error."""
    collection.insert_many(SINGLE_DOC)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": 5,
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
    assertFailureCode(result, TYPE_MISMATCH_ERROR, msg="sortBy: 5 (non-object) rejected")


def test_sortby_string(collection):
    """$setWindowFields with sortBy: "invalid" (string) produces error."""
    collection.insert_many(SINGLE_DOC)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": "invalid",
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
    assertFailureCode(result, TYPE_MISMATCH_ERROR, msg="sortBy: string (non-object) rejected")


def test_sortby_array(collection):
    """$setWindowFields with sortBy: [1] (array) produces error."""
    collection.insert_many(SINGLE_DOC)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": [1],
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
    assertFailureCode(result, TYPE_MISMATCH_ERROR, msg="sortBy: array (non-object) rejected")


def test_sortby_null(collection):
    """$setWindowFields with sortBy: null is valid — treated as omitted."""
    collection.insert_many(SINGLE_DOC)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": None,
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
    expected = [{"_id": 1, "partition": "A", "value": 10, "result": 10}]
    assertSuccess(result, expected, msg="sortBy: null treated as omitted")


def test_sortby_boolean(collection):
    """$setWindowFields with sortBy: true (boolean) produces error."""
    collection.insert_many(SINGLE_DOC)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": True,
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
    assertFailureCode(result, TYPE_MISMATCH_ERROR, msg="sortBy: boolean (non-object) rejected")


# Property [SortBy Empty Object]: sortBy = {} is valid — treated as no sort


def test_sortby_empty_object(collection):
    """$setWindowFields with sortBy: {} (empty object) is valid — treated as no sort."""
    collection.insert_many(SINGLE_DOC)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": {},
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
    expected = [{"_id": 1, "partition": "A", "value": 10, "result": 10}]
    assertSuccess(result, expected, msg="sortBy: {} treated as no sort")


# Property [SortBy Direction Validation]: sortBy direction must be 1 or -1


def test_sortby_direction_zero(collection):
    """$setWindowFields with sortBy direction 0 produces error."""
    collection.insert_many(SINGLE_DOC)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": {"_id": 0},
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
    assertFailureCode(result, 15975, msg="sortBy direction 0 rejected")


def test_sortby_direction_two(collection):
    """$setWindowFields with sortBy direction 2 produces error."""
    collection.insert_many(SINGLE_DOC)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": {"_id": 2},
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
    assertFailureCode(result, 15975, msg="sortBy direction 2 rejected")


def test_sortby_direction_negative_two(collection):
    """$setWindowFields with sortBy direction -2 produces error."""
    collection.insert_many(SINGLE_DOC)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": {"_id": -2},
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
    assertFailureCode(result, 15975, msg="sortBy direction -2 rejected")


def test_sortby_direction_string(collection):
    """$setWindowFields with sortBy direction as string produces error."""
    collection.insert_many(SINGLE_DOC)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": {"_id": "asc"},
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
    assertFailureCode(result, 15974, msg="sortBy direction 'asc' (string) rejected")


# Property [Window Empty Document]: window = {} is valid — defaults to unbounded


def test_window_empty_document(collection):
    """$setWindowFields with window: {} (empty document) is valid — defaults to unbounded."""
    collection.insert_many(SINGLE_DOC)
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
                                "window": {},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    expected = [{"_id": 1, "partition": "A", "value": 10, "result": 10}]
    assertSuccess(result, expected, msg="window: {} defaults to unbounded")


# Property [Window Scalar]: window = scalar (non-document, non-array) must be rejected


def test_window_integer_scalar(collection):
    """$setWindowFields with window: 5 (integer scalar) produces error."""
    collection.insert_many(SINGLE_DOC)
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
                                "window": 5,
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, FAILED_TO_PARSE_ERROR, msg="window: 5 (integer scalar) rejected")


def test_window_boolean_scalar(collection):
    """$setWindowFields with window: true (boolean scalar) produces error."""
    collection.insert_many(SINGLE_DOC)
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
                                "window": True,
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, FAILED_TO_PARSE_ERROR, msg="window: true (boolean scalar) rejected")
