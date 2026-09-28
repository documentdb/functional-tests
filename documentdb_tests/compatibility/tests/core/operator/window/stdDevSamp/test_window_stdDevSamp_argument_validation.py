"""
Tests for $stdDevSamp argument validation in window context.

Covers: valid expression forms (field path, operator expression, literal),
non-numeric literal inputs that return null, invalid argument shapes that
produce parse errors (unknown keys in output field spec, multiple accumulators,
empty output field, multi-key expression objects, unknown operators in
expression, and field path with empty component).
"""

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import (
    EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
    FAILED_TO_PARSE_ERROR,
    FIELD_PATH_EMPTY_COMPONENT_ERROR,
    UNRECOGNIZED_EXPRESSION_ERROR,
)
from documentdb_tests.framework.executor import execute_command

TWO_DOCS = [
    {"_id": 1, "partition": "A", "value": 10},
    {"_id": 2, "partition": "A", "value": 20},
]

SINGLE_DOC = [{"_id": 1, "partition": "A", "value": 10}]

# Property [Valid Expression Forms]: accepted expression inputs


def test_stdDevSamp_field_path_expression(collection):
    """$stdDevSamp accepts a field path expression."""
    collection.insert_many(TWO_DOCS)
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


# Property [Non-Numeric Literal Inputs]: non-numeric constants return null (not errors)


def test_stdDevSamp_empty_string_expression(collection):
    """$stdDevSamp with empty string (not a valid field path) — treated as non-numeric."""
    collection.insert_many(TWO_DOCS)
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


def test_stdDevSamp_array_multiple_expressions_returns_null(collection):
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


def test_stdDevSamp_boolean_literal_returns_null(collection):
    """$stdDevSamp with boolean literal — non-numeric constant, returns null."""
    collection.insert_many(TWO_DOCS)
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
                                "$stdDevSamp": True,
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
        {"_id": 1, "partition": "A", "value": 10, "result": None},
        {"_id": 2, "partition": "A", "value": 20, "result": None},
    ]
    assertSuccess(result, expected, msg="boolean literal treated as non-numeric, returns null")


def test_stdDevSamp_null_literal_returns_null(collection):
    """$stdDevSamp with null literal — returns null."""
    collection.insert_many(TWO_DOCS)
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
                                "$stdDevSamp": None,
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
        {"_id": 1, "partition": "A", "value": 10, "result": None},
        {"_id": 2, "partition": "A", "value": 20, "result": None},
    ]
    assertSuccess(result, expected, msg="null literal returns null")


def test_stdDevSamp_empty_object_returns_null(collection):
    """$stdDevSamp with empty object {} — treated as non-numeric, returns null."""
    collection.insert_many(TWO_DOCS)
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
                                "$stdDevSamp": {},
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
        {"_id": 1, "partition": "A", "value": 10, "result": None},
        {"_id": 2, "partition": "A", "value": 20, "result": None},
    ]
    assertSuccess(result, expected, msg="empty object treated as non-numeric, returns null")


# Property [Invalid Argument Shapes - Parse Errors]: inputs that produce errors at parse time


def test_stdDevSamp_unknown_key_in_output_field_errors(collection):
    """Unknown key alongside $stdDevSamp in output field spec produces parse error."""
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
                                "$stdDevSamp": "$value",
                                "window": {"documents": ["unbounded", "unbounded"]},
                                "unknownKey": 1,
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(
        result, FAILED_TO_PARSE_ERROR, msg="unknown key alongside $stdDevSamp rejected"
    )


def test_stdDevSamp_unknown_key_errors_on_empty_collection(collection):
    """Parse-time error fires on empty collection — no documents needed."""
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
                                "unknownKey": 1,
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(
        result,
        FAILED_TO_PARSE_ERROR,
        msg="parse-time error fires on empty collection",
    )


def test_stdDevSamp_multiple_accumulators_in_output_field_errors(collection):
    """Multiple accumulators in same output field spec produces parse error."""
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
                                "$stdDevSamp": "$value",
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
    assertFailureCode(
        result,
        FAILED_TO_PARSE_ERROR,
        msg="multiple accumulators in output field rejected",
    )


def test_stdDevSamp_no_accumulator_in_output_field_errors(collection):
    """Output field with no accumulator (only window key) produces parse error."""
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
                                "window": {"documents": ["unbounded", "unbounded"]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, FAILED_TO_PARSE_ERROR, msg="no accumulator in output field rejected")


def test_stdDevSamp_multi_key_expression_object_errors(collection):
    """$stdDevSamp with multi-key expression object (ambiguous) produces error."""
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
                                "$stdDevSamp": {"$add": [1, 2], "$subtract": [3, 1]},
                                "window": {"documents": ["unbounded", "unbounded"]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(
        result,
        EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
        msg="multi-key expression object rejected",
    )


def test_stdDevSamp_unrecognized_expression_operator_errors(collection):
    """$stdDevSamp with unrecognized expression operator produces error."""
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
                                "$stdDevSamp": {"$unknownOp": "$value"},
                                "window": {"documents": ["unbounded", "unbounded"]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(
        result,
        UNRECOGNIZED_EXPRESSION_ERROR,
        msg="unrecognized expression operator rejected",
    )


def test_stdDevSamp_field_path_empty_component_errors(collection):
    """$stdDevSamp with field path containing empty component produces error."""
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
                                "$stdDevSamp": "$a..b",
                                "window": {"documents": ["unbounded", "unbounded"]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(
        result,
        FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="field path with empty component rejected",
    )
