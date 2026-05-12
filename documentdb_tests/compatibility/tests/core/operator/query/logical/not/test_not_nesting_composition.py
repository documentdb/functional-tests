"""
Tests for $not query operator nesting and composition with logical operators.

Covers $not inside $and, $or, $nor, nested $not error case,
and multiple $not on same field.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

NESTING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="not_inside_or",
        filter={"$or": [{"a": {"$not": {"$gt": 10}}}, {"b": {"$not": {"$lt": 5}}}]},
        doc=[
            {"_id": 1, "a": 5, "b": 3},
            {"_id": 2, "a": 15, "b": 10},
            {"_id": 3, "a": 15, "b": 3},
        ],
        expected=[{"_id": 1, "a": 5, "b": 3}, {"_id": 2, "a": 15, "b": 10}],
        msg="$not inside $or should match docs satisfying either negated condition",
    ),
    QueryTestCase(
        id="not_inside_nor",
        filter={"$nor": [{"a": {"$not": {"$gt": 10}}}]},
        doc=[{"_id": 1, "a": 5}, {"_id": 2, "a": 15}, {"_id": 3, "a": 25}],
        expected=[{"_id": 2, "a": 15}, {"_id": 3, "a": 25}],
        msg="$nor with $not should return docs where a > 10 (triple negation)",
    ),
    QueryTestCase(
        id="multiple_not_on_same_field_via_and",
        filter={"$and": [{"val": {"$not": {"$lt": 0}}}, {"val": {"$not": {"$gt": 100}}}]},
        doc=[
            {"_id": 1, "val": -5},
            {"_id": 2, "val": 50},
            {"_id": 3, "val": 150},
        ],
        expected=[{"_id": 2, "val": 50}],
        msg="Multiple $not via $and should create range 0 <= val <= 100",
    ),
    QueryTestCase(
        id="nested_not_not_double_negation",
        filter={"val": {"$not": {"$not": {"$gt": 10}}}},
        doc=[{"_id": 1, "val": 5}, {"_id": 2, "val": 15}],
        expected=[{"_id": 2, "val": 15}],
        msg="Nested $not $not acts as double negation equivalent to the inner condition",
    ),
]

ALL_TESTS = NESTING_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_not_nesting_composition(collection, test):
    """Test $not query operator nesting and composition with logical operators."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        ignore_doc_order=True,
        msg=test.msg,
    )
