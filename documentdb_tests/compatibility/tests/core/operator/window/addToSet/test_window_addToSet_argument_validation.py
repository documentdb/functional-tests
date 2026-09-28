"""
Tests for $addToSet argument validation in window context.

$addToSet accepts any expression as its single argument and collects the value,
so this covers the accepted expression forms (field path, operator, literal,
array, object) and the output-field / expression shapes that produce parse
errors. Set-valued results are compared with ignore_order_in=["result"].
"""

from documentdb_tests.compatibility.tests.core.operator.window.utils.window_test_case import (
    run_window_operator,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import (
    EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
    FAILED_TO_PARSE_ERROR,
    FIELD_PATH_EMPTY_COMPONENT_ERROR,
    UNRECOGNIZED_EXPRESSION_ERROR,
)
from documentdb_tests.framework.executor import execute_command

WHOLE = {"documents": ["unbounded", "unbounded"]}

TWO_DOCS = [
    {"_id": 1, "partition": "A", "value": 10},
    {"_id": 2, "partition": "A", "value": 20},
]

SINGLE_DOC = [{"_id": 1, "partition": "A", "value": 10}]

# Property [Valid Expression Forms]: $addToSet accepts any expression and collects its value.


def test_addToSet_field_path_expression(collection):
    """$addToSet accepts a field path expression and collects the field values."""
    result = run_window_operator(collection, "$addToSet", TWO_DOCS, WHOLE, expression="$value")
    expected = [
        {"_id": 1, "partition": "A", "value": 10, "result": [10, 20]},
        {"_id": 2, "partition": "A", "value": 20, "result": [10, 20]},
    ]
    assertSuccess(
        result, expected, msg="field path expression accepted", ignore_order_in=["result"]
    )


def test_addToSet_operator_expression(collection):
    """$addToSet accepts an operator expression and collects the computed values."""
    result = run_window_operator(
        collection, "$addToSet", TWO_DOCS, WHOLE, expression={"$add": ["$value", 1]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": 10, "result": [11, 21]},
        {"_id": 2, "partition": "A", "value": 20, "result": [11, 21]},
    ]
    assertSuccess(result, expected, msg="operator expression accepted", ignore_order_in=["result"])


def test_addToSet_literal_constant_expression(collection):
    """$addToSet with a literal constant — every row contributes the same value, deduped to one."""
    result = run_window_operator(
        collection, "$addToSet", TWO_DOCS, WHOLE, expression={"$literal": 42}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": 10, "result": [42]},
        {"_id": 2, "partition": "A", "value": 20, "result": [42]},
    ]
    assertSuccess(
        result, expected, msg="literal constant collected and deduped", ignore_order_in=["result"]
    )


def test_addToSet_array_expression(collection):
    """$addToSet with an array expression collects the whole array as a single element."""
    docs = [
        {"_id": 1, "partition": "A", "x": 10, "y": 20},
        {"_id": 2, "partition": "A", "x": 10, "y": 99},
    ]
    result = run_window_operator(collection, "$addToSet", docs, WHOLE, expression=["$x", "$y"])
    expected = [
        {"_id": 1, "partition": "A", "x": 10, "y": 20, "result": [[10, 20], [10, 99]]},
        {"_id": 2, "partition": "A", "x": 10, "y": 99, "result": [[10, 20], [10, 99]]},
    ]
    assertSuccess(
        result,
        expected,
        msg="array expression collected as one element",
        ignore_order_in=["result"],
    )


def test_addToSet_object_expression(collection):
    """$addToSet with an object expression collects the object; equal objects dedup to one."""
    docs = [
        {"_id": 1, "partition": "A", "x": 10},
        {"_id": 2, "partition": "A", "x": 10},
    ]
    result = run_window_operator(collection, "$addToSet", docs, WHOLE, expression={"a": "$x"})
    expected = [
        {"_id": 1, "partition": "A", "x": 10, "result": [{"a": 10}]},
        {"_id": 2, "partition": "A", "x": 10, "result": [{"a": 10}]},
    ]
    assertSuccess(
        result, expected, msg="object expression collected and deduped", ignore_order_in=["result"]
    )


# Property [Invalid Argument Shapes - Parse Errors]: inputs that produce errors at parse time.


def test_addToSet_unknown_key_in_output_field_errors(collection):
    """Unknown key alongside $addToSet in output field spec produces parse error."""
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
                                "$addToSet": "$value",
                                "window": WHOLE,
                                "unknownKey": 1,
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, FAILED_TO_PARSE_ERROR, msg="unknown key alongside $addToSet rejected")


def test_addToSet_unknown_key_errors_on_empty_collection(collection):
    """Parse-time error fires on an empty collection — no documents needed."""
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
                                "$addToSet": "$value",
                                "window": WHOLE,
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
        result, FAILED_TO_PARSE_ERROR, msg="parse-time error fires on empty collection"
    )


def test_addToSet_multiple_accumulators_in_output_field_errors(collection):
    """Multiple accumulators in the same output field spec produces parse error."""
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
                                "$addToSet": "$value",
                                "$sum": "$value",
                                "window": WHOLE,
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(
        result, FAILED_TO_PARSE_ERROR, msg="multiple accumulators in output field rejected"
    )


def test_addToSet_no_accumulator_in_output_field_errors(collection):
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
                        "output": {"result": {"window": WHOLE}},
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, FAILED_TO_PARSE_ERROR, msg="no accumulator in output field rejected")


def test_addToSet_multi_key_expression_object_errors(collection):
    """$addToSet with a multi-key expression object (ambiguous) produces error."""
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
                                "$addToSet": {"$add": [1, 2], "$subtract": [3, 1]},
                                "window": WHOLE,
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(
        result, EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR, msg="multi-key expression object rejected"
    )


def test_addToSet_unrecognized_expression_operator_errors(collection):
    """$addToSet with an unrecognized expression operator produces error."""
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
                                "$addToSet": {"$unknownOp": "$value"},
                                "window": WHOLE,
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(
        result, UNRECOGNIZED_EXPRESSION_ERROR, msg="unrecognized expression operator rejected"
    )


def test_addToSet_field_path_empty_component_errors(collection):
    """$addToSet with a field path containing an empty component produces error."""
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
                                "$addToSet": "$a..b",
                                "window": WHOLE,
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(
        result, FIELD_PATH_EMPTY_COMPONENT_ERROR, msg="field path with empty component rejected"
    )
