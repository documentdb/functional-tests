"""
Tests for $covariancePop argument validation in window context.

Covers: valid expression forms (array of two field paths, operator expressions),
invalid argument shapes that produce null results (not an array, wrong length,
single expression, three expressions, empty array, object expression),
and structural errors (unknown keys in output field spec, multiple accumulators).

Server behavior (verified): $covariancePop does NOT reject bad argument
shapes at parse time. Invalid forms (single expression, wrong-length arrays,
objects, empty arrays) all succeed and return null for every document.
Only structural $setWindowFields errors (unknown keys, multiple accumulators,
no accumulator, bad field paths, unrecognized operators) produce parse errors.
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

TWO_DOCS = [
    {"_id": 1, "partition": "A", "x": 1, "y": 2},
    {"_id": 2, "partition": "A", "x": 2, "y": 4},
]

SINGLE_DOC = [{"_id": 1, "partition": "A", "x": 1, "y": 2}]

# Property [Valid Expression Forms]: accepted expression inputs


def test_covariancePop_two_field_paths(collection):
    """$covariancePop accepts array of two field path expressions."""
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs=TWO_DOCS,
        expression=["$x", "$y"],
        window={"documents": ["unbounded", "unbounded"]},
    )
    # x=[1,2], y=[2,4]: mean_x=1.5, mean_y=3
    # covPop = ((-0.5)(-1)+(0.5)(1))/2 = 1/2 = 0.5
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": 0.5},
        {"_id": 2, "partition": "A", "x": 2, "y": 4, "result": 0.5},
    ]
    assertSuccess(result, expected, msg="two field path expressions accepted")


def test_covariancePop_operator_expressions(collection):
    """$covariancePop accepts operator expressions within the array."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2},
        {"_id": 2, "partition": "A", "x": 2, "y": 4},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs=docs,
        expression=[{"$multiply": ["$x", 2]}, {"$multiply": ["$y", 2]}],
        window={"documents": ["unbounded", "unbounded"]},
    )
    # x*2=[2,4], y*2=[4,8]: mean_x=3, mean_y=6
    # covPop = ((-1)(-2)+(1)(2))/2 = 4/2 = 2.0
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": 2.0},
        {"_id": 2, "partition": "A", "x": 2, "y": 4, "result": 2.0},
    ]
    assertSuccess(result, expected, msg="operator expressions within array accepted")


def test_covariancePop_same_field_both_positions(collection):
    """$covariancePop with same field in both positions equals varPop."""
    docs = [
        {"_id": 1, "partition": "A", "x": 10},
        {"_id": 2, "partition": "A", "x": 20},
        {"_id": 3, "partition": "A", "x": 30},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs=docs,
        expression=["$x", "$x"],
        window={"documents": ["unbounded", "unbounded"]},
    )
    # covPop(x,x) = varPop(x) = 200/3 = 66.6667
    expected = [
        {"_id": 1, "partition": "A", "x": 10, "result": 66.66666666666667},
        {"_id": 2, "partition": "A", "x": 20, "result": 66.66666666666667},
        {"_id": 3, "partition": "A", "x": 30, "result": 66.66666666666667},
    ]
    assertSuccess(result, expected, msg="same field both positions equals varPop")


def test_covariancePop_literal_numeric_expressions(collection):
    """$covariancePop with literal numeric values — constant values produce covPop=0."""
    docs = [
        {"_id": 1, "partition": "A", "x": 10},
        {"_id": 2, "partition": "A", "x": 20},
        {"_id": 3, "partition": "A", "x": 30},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs=docs,
        expression=[{"$literal": 5}, {"$literal": 10}],
        window={"documents": ["unbounded", "unbounded"]},
    )
    # All rows have same pair (5,10) -> covPop = 0
    expected = [
        {"_id": 1, "partition": "A", "x": 10, "result": 0.0},
        {"_id": 2, "partition": "A", "x": 20, "result": 0.0},
        {"_id": 3, "partition": "A", "x": 30, "result": 0.0},
    ]
    assertSuccess(result, expected, msg="literal numeric expressions produce 0 covPop")


# Property [Invalid Argument Shapes Return Null]: Server does NOT reject these at parse time


def test_covariancePop_single_expression_not_array_returns_null(collection):
    """$covariancePop with single field path (not array) returns null for all docs."""
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs=TWO_DOCS,
        expression="$x",
        window={"documents": ["unbounded", "unbounded"]},
    )
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": None},
        {"_id": 2, "partition": "A", "x": 2, "y": 4, "result": None},
    ]
    assertSuccess(result, expected, msg="single field path (not array) returns null")


def test_covariancePop_single_element_array_returns_null(collection):
    """$covariancePop with array of only 1 expression returns null for all docs."""
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs=TWO_DOCS,
        expression=["$x"],
        window={"documents": ["unbounded", "unbounded"]},
    )
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": None},
        {"_id": 2, "partition": "A", "x": 2, "y": 4, "result": None},
    ]
    assertSuccess(result, expected, msg="array of 1 expression returns null")


def test_covariancePop_three_element_array_returns_null(collection):
    """$covariancePop with array of 3 expressions returns null for all docs."""
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs=TWO_DOCS,
        expression=["$x", "$y", "$x"],
        window={"documents": ["unbounded", "unbounded"]},
    )
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": None},
        {"_id": 2, "partition": "A", "x": 2, "y": 4, "result": None},
    ]
    assertSuccess(result, expected, msg="array of 3 expressions returns null")


def test_covariancePop_empty_array_returns_null(collection):
    """$covariancePop with empty array [] returns null for all docs."""
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs=TWO_DOCS,
        expression=[],
        window={"documents": ["unbounded", "unbounded"]},
    )
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": None},
        {"_id": 2, "partition": "A", "x": 2, "y": 4, "result": None},
    ]
    assertSuccess(result, expected, msg="empty array returns null")


def test_covariancePop_object_expression_returns_null(collection):
    """$covariancePop with object (not array) as argument returns null for all docs."""
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs=TWO_DOCS,
        expression={"$add": ["$x", 1]},
        window={"documents": ["unbounded", "unbounded"]},
    )
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": None},
        {"_id": 2, "partition": "A", "x": 2, "y": 4, "result": None},
    ]
    assertSuccess(result, expected, msg="object (not array) as argument returns null")


# Property [Structural Parse Errors]: errors in $setWindowFields output spec structure


def test_covariancePop_unknown_key_in_output_field_errors(collection):
    """Unknown key alongside $covariancePop in output field spec produces parse error."""
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
                                "$covariancePop": ["$x", "$y"],
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
        result, FAILED_TO_PARSE_ERROR, msg="unknown key alongside $covariancePop rejected"
    )


def test_covariancePop_unknown_key_errors_on_empty_collection(collection):
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
                                "$covariancePop": ["$x", "$y"],
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


def test_covariancePop_multiple_accumulators_in_output_field_errors(collection):
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
                                "$covariancePop": ["$x", "$y"],
                                "$sum": "$x",
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


def test_covariancePop_no_accumulator_in_output_field_errors(collection):
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


def test_covariancePop_unrecognized_expression_operator_in_array_errors(collection):
    """$covariancePop with unrecognized expression operator in array element produces error."""
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
                                "$covariancePop": [{"$unknownOp": "$x"}, "$y"],
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
        msg="unrecognized expression operator in array rejected",
    )


def test_covariancePop_field_path_empty_component_errors(collection):
    """$covariancePop with field path containing empty component produces error."""
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
                                "$covariancePop": ["$a..b", "$y"],
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


def test_covariancePop_multi_field_expression_object_errors(collection):
    """$covariancePop with multi-field expression object in array element produces error."""
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
                                "$covariancePop": [
                                    {"$add": ["$x", 1], "$multiply": ["$x", 2]},
                                    "$y",
                                ],
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
        msg="multi-field expression object in array element rejected",
    )
