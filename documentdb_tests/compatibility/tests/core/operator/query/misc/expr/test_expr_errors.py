"""
Tests for $expr error handling.

Covers invalid expressions, dollar sign parsing errors, undefined variable
references, $expr in arrayFilters, $expr in $elemMatch query and projection,
query operators rejected inside $expr, and runtime error propagation.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    EXPR_IN_ARRAY_FILTERS_ERROR,
    EXPRESSION_IN_NOT_ARRAY_ERROR,
    EXPRESSION_TYPE_MISMATCH_ERROR,
    FAILED_TO_PARSE_ERROR,
    INVALID_DOLLAR_FIELD_PATH,
    LET_UNDEFINED_VARIABLE_ERROR,
    UNRECOGNIZED_EXPRESSION_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

ALL_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="invalid_operator",
        doc=[{"_id": 1}],
        filter={"$expr": {"$invalidOp": 1}},
        error_code=UNRECOGNIZED_EXPRESSION_ERROR,
        msg="$expr with invalid aggregation operator",
    ),
    QueryTestCase(
        id="bare_dollar",
        doc=[{"_id": 1}],
        filter={"$expr": {"$eq": ["$", 1]}},
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$expr with bare '$' — invalid field path",
    ),
    QueryTestCase(
        id="bare_double_dollar",
        doc=[{"_id": 1}],
        filter={"$expr": {"$eq": ["$$", 1]}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$expr with bare '$$' — empty variable name",
    ),
    QueryTestCase(
        id="undefined_variable",
        doc=[{"_id": 1}],
        filter={"$expr": {"$eq": ["$$undefined_var", 1]}},
        error_code=LET_UNDEFINED_VARIABLE_ERROR,
        msg="$expr referencing undefined variable",
    ),
    QueryTestCase(
        id="rejects_query_gt",
        doc=[{"_id": 1, "a": 5}],
        filter={"$expr": {"a": {"$gt": 5}}},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="query-style $gt rejected inside $expr",
    ),
    QueryTestCase(
        id="rejects_query_in",
        doc=[{"_id": 1, "a": 5}],
        filter={"$expr": {"a": {"$in": [1, 2]}}},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="query-style $in rejected inside $expr",
    ),
    QueryTestCase(
        id="rejects_query_exists",
        doc=[{"_id": 1, "a": 5}],
        filter={"$expr": {"a": {"$exists": True}}},
        error_code=UNRECOGNIZED_EXPRESSION_ERROR,
        msg="query-style $exists rejected inside $expr",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_expr_errors(collection, test):
    """Test $expr error handling."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertResult(result, expected=test.expected, error_code=test.error_code, msg=test.msg)


def test_expr_in_array_filters(collection):
    """Test $expr used inside arrayFilters — should fail."""
    collection.insert_one({"_id": 1, "arr": [1, 2, 3]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$set": {"arr.$[elem]": 0}},
                    "arrayFilters": [{"$expr": {"$gt": ["$elem", 1]}}],
                }
            ],
        },
    )
    assertFailureCode(result, EXPR_IN_ARRAY_FILTERS_ERROR)


def test_expr_in_elemmatch_query(collection):
    """Test $expr inside $elemMatch in query position — should fail."""
    collection.insert_one({"_id": 1, "arr": [{"x": 1}, {"x": 5}]})
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"arr": {"$elemMatch": {"$expr": {"$gt": ["$x", 3]}}}},
        },
    )
    assertFailureCode(result, BAD_VALUE_ERROR)


def test_expr_in_elemmatch_projection(collection):
    """Test $expr inside $elemMatch in projection position — should fail."""
    collection.insert_one({"_id": 1, "arr": [{"x": 1}, {"x": 5}]})
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"_id": 1},
            "projection": {"arr": {"$elemMatch": {"$expr": {"$gt": ["$x", 3]}}}},
        },
    )
    assertFailureCode(result, BAD_VALUE_ERROR)


def test_expr_runtime_error_when_document_matches(collection):
    """Test $expr evaluates expression on matching documents — runtime error propagates."""
    collection.insert_one({"_id": 1, "a": 10, "b": 0})
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"a": 10, "$expr": {"$gt": [{"$divide": ["$a", "$b"]}, 0]}},
        },
    )
    assertFailureCode(result, BAD_VALUE_ERROR)
