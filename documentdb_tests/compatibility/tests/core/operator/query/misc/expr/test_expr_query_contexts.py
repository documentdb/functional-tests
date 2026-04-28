"""
Tests for $expr in find query contexts.

Covers find with logical operators, cursor operations, array field behavior,
and $expr-specific semantics.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

BASIC_DOCS = [
    {"_id": 1, "a": 5, "b": 3},
    {"_id": 2, "a": 1, "b": 10},
    {"_id": 3, "a": -1, "b": 0},
]


FIND_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="combined_with_standard_query",
        doc=BASIC_DOCS,
        filter={"$expr": {"$gt": ["$a", 0]}, "b": {"$lt": 10}},
        expected=[{"_id": 1, "a": 5, "b": 3}],
        msg="$expr combined with standard query operator",
    ),
    QueryTestCase(
        id="or_two_exprs",
        doc=BASIC_DOCS,
        filter={"$or": [{"$expr": {"$gt": ["$a", 100]}}, {"$expr": {"$lt": ["$a", 0]}}]},
        expected=[{"_id": 3, "a": -1, "b": 0}],
        msg="$or with two $expr clauses",
    ),
    QueryTestCase(
        id="and_two_exprs",
        doc=BASIC_DOCS,
        filter={"$and": [{"$expr": {"$gt": ["$a", 0]}}, {"$expr": {"$lt": ["$b", 10]}}]},
        expected=[{"_id": 1, "a": 5, "b": 3}],
        msg="$and with two $expr clauses",
    ),
    QueryTestCase(
        id="nor_single_expr",
        doc=BASIC_DOCS,
        filter={"$nor": [{"$expr": {"$gt": ["$a", 0]}}]},
        expected=[{"_id": 3, "a": -1, "b": 0}],
        msg="$nor with $expr — matches docs where expression is false",
    ),
    QueryTestCase(
        id="nor_two_exprs",
        doc=BASIC_DOCS,
        filter={"$nor": [{"$expr": {"$gt": ["$a", 0]}}, {"$expr": {"$lt": ["$a", 0]}}]},
        expected=[],
        msg="$nor with two $expr clauses — excludes docs matching either",
    ),
    QueryTestCase(
        id="array_no_implicit_matching",
        doc=[{"_id": 1, "a": [1, 5, 10, 15]}],
        filter={"$expr": {"$gt": ["$a", 12]}},
        expected=[{"_id": 1, "a": [1, 5, 10, 15]}],
        msg="$expr does NOT do implicit array element matching",
    ),
    QueryTestCase(
        id="result_not_projected",
        doc=[{"_id": 1, "a": 5, "b": 8}],
        filter={"$expr": {"$gt": [{"$add": ["$a", "$b"]}, 10]}},
        expected=[{"_id": 1, "a": 5, "b": 8}],
        msg="$expr only filters — computed values don't appear in output",
    ),
]

ALL_TESTS = FIND_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_expr_query_contexts(collection, test):
    """Test $expr in find with various query patterns."""
    if test.doc:
        collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertResult(result, expected=test.expected, error_code=test.error_code, msg=test.msg)


def test_expr_with_sort(collection):
    """Test find with $expr + sort."""
    collection.insert_many(BASIC_DOCS)
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"$expr": {"$gt": ["$a", 0]}},
            "sort": {"a": -1},
        },
    )
    assertSuccess(result, [{"_id": 1, "a": 5, "b": 3}, {"_id": 2, "a": 1, "b": 10}])


def test_expr_with_limit(collection):
    """Test find with $expr + limit."""
    collection.insert_many(BASIC_DOCS)
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"$expr": {"$gt": ["$a", 0]}},
            "sort": {"_id": 1},
            "limit": 1,
        },
    )
    assertSuccess(result, [{"_id": 1, "a": 5, "b": 3}])


def test_expr_with_projection(collection):
    """Test find with $expr + projection."""
    collection.insert_many(BASIC_DOCS)
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"$expr": {"$gt": ["$a", 0]}},
            "projection": {"a": 1, "_id": 0},
        },
    )
    assertSuccess(result, [{"a": 5}, {"a": 1}], ignore_doc_order=True)


def test_expr_with_skip(collection):
    """Test find with $expr + skip."""
    collection.insert_many(BASIC_DOCS)
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"$expr": {"$gt": ["$a", 0]}},
            "sort": {"_id": 1},
            "skip": 1,
        },
    )
    assertSuccess(result, [{"_id": 2, "a": 1, "b": 10}])
