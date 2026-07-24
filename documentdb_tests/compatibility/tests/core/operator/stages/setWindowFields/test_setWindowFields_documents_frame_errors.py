"""
Tests for $setWindowFields documents-mode window frame validation errors.

These are operator-agnostic — frame spec validation happens before the
accumulator runs. Uses $sum as the simplest accumulator.

Covers: null window value, window as non-object types, unknown keys in window
object, document-bound validation errors (typo strings, wrong-length arrays,
null bounds, boolean bounds, non-object window, lower > upper, fractional
bounds), unknown accumulator keys, and specifying both documents and range.
"""

from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    FAILED_TO_PARSE_ERROR,
    MISSING_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command

# Property [Window Type Validation]: window value must be an object


def test_window_null_value(collection):
    """window: null produces error."""
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
                        "sortBy": {"_id": 1},
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": None,
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, FAILED_TO_PARSE_ERROR, msg="window: null rejected")


def test_window_array_value(collection):
    """window as array produces error."""
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
                        "sortBy": {"_id": 1},
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": [-1, 0],
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, FAILED_TO_PARSE_ERROR, msg="window as array rejected")


def test_window_not_object(collection):
    """Window value that is a string produces error."""
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
                        "sortBy": {"_id": 1},
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": "invalid",
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, FAILED_TO_PARSE_ERROR, msg="window not an object rejected")


def test_window_unknown_key(collection):
    """Unknown key in window object produces error."""
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
                                "$sum": "$value",
                                "window": {"documents": [0, 1], "bogus": 123},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, FAILED_TO_PARSE_ERROR, msg="unknown key in window object rejected")


# Property [Document Bounds Validation]: document bounds array must be well-formed


def test_documents_bounds_null_lower(collection):
    """Null as lower document bound produces error."""
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
                        "sortBy": {"_id": 1},
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": {"documents": [None, 0]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, FAILED_TO_PARSE_ERROR, msg="null lower bound rejected")


def test_documents_bounds_null_upper(collection):
    """Null as upper document bound produces error."""
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
                        "sortBy": {"_id": 1},
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": {"documents": [0, None]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, FAILED_TO_PARSE_ERROR, msg="null upper bound rejected")


def test_documents_bounds_empty_array(collection):
    """Empty bounds array produces error."""
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
                        "sortBy": {"_id": 1},
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": {"documents": []},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, FAILED_TO_PARSE_ERROR, msg="empty bounds array rejected")


def test_documents_bounds_three_elements(collection):
    """Three-element bounds array produces error."""
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
                        "sortBy": {"_id": 1},
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": {"documents": [-1, 0, 1]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, FAILED_TO_PARSE_ERROR, msg="three-element bounds array rejected")


def test_documents_bounds_boolean(collection):
    """Boolean as document bound produces error."""
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
                        "sortBy": {"_id": 1},
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": {"documents": [True, 0]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, FAILED_TO_PARSE_ERROR, msg="boolean document bound rejected")


def test_bound_typo_string(collection):
    """Invalid bound string (not 'current' or 'unbounded') produces error."""
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
                        "sortBy": {"_id": 1},
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": {"documents": ["invalid", 0]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, FAILED_TO_PARSE_ERROR, msg="invalid bound string rejected")


def test_bounds_wrong_length(collection):
    """Bounds array with wrong length (1 element) produces error."""
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
                        "sortBy": {"_id": 1},
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": {"documents": ["unbounded"]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, FAILED_TO_PARSE_ERROR, msg="bounds array wrong length rejected")


def test_fractional_document_bound(collection):
    """Fractional document bound produces error."""
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
                        "sortBy": {"_id": 1},
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": {"documents": [-1.5, 0]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, FAILED_TO_PARSE_ERROR, msg="fractional document bound rejected")


# Property [Bound Ordering]: lower bound must not exceed upper bound


def test_lower_exceeds_upper(collection):
    """Document bounds with lower > upper produces error 5339900."""
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
                        "sortBy": {"_id": 1},
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": {"documents": [1, -1]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, 5339900, msg="documents lower > upper rejected")


# Property [Conflicting Modes]: cannot specify both documents and range


def test_both_documents_and_range(collection):
    """Specifying both documents and range produces error."""
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
                        "sortBy": {"_id": 1},
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": {"documents": [-1, 0], "range": [-1, 0]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, FAILED_TO_PARSE_ERROR, msg="both documents and range rejected")


# Property [Output Field Validation]: output field spec must be well-formed


def test_output_field_unknown_accumulator_key(collection):
    """Unknown key alongside accumulator in output field produces error."""
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
                        "sortBy": {"_id": 1},
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": {"documents": [-1, 0]},
                                "bogus": 1,
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(
        result, FAILED_TO_PARSE_ERROR, msg="unknown key in output field spec rejected"
    )


# Property [Stage Document Validation]: $setWindowFields stage document must be well-formed


def test_stage_unknown_top_level_key(collection):
    """Unknown top-level key in $setWindowFields stage document produces error."""
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
                        "sortBy": {"_id": 1},
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": {"documents": ["unbounded", "unbounded"]},
                            }
                        },
                        "unknownKey": 1,
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(
        result, UNRECOGNIZED_COMMAND_FIELD_ERROR, msg="unknown top-level key in stage rejected"
    )


def test_stage_output_omitted(collection):
    """$setWindowFields without output field produces error."""
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
                        "sortBy": {"_id": 1},
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, MISSING_FIELD_ERROR, msg="output omitted rejected")


def test_stage_output_non_document(collection):
    """$setWindowFields with non-document output produces error."""
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
                        "sortBy": {"_id": 1},
                        "output": "invalid",
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, TYPE_MISMATCH_ERROR, msg="non-document output rejected")


# Property [SortBy Required For Bounded Windows]: bounded documents-mode windows require sortBy


def test_bounded_documents_window_without_sortby(collection):
    """Bounded documents window [-1, 1] without sortBy produces error."""
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
                                "window": {"documents": [-1, 1]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, 5339901, msg="bounded documents window without sortBy rejected")


def test_cumulative_documents_window_without_sortby(collection):
    """Cumulative documents window [unbounded, current] without sortBy produces error."""
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
                                "window": {"documents": ["unbounded", "current"]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, 5339901, msg="cumulative documents window without sortBy rejected")
