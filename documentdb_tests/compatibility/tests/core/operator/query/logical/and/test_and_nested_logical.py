"""
Tests for nested $and with other logical operators.

Tests nested $and, $and containing $or/$nor, and short-circuit behavior.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

DOCS = [
    {"_id": 1, "a": 1, "b": 2, "c": 3},
    {"_id": 2, "a": 2, "b": 2, "c": 3},
    {"_id": 3, "a": 1, "b": 3, "c": 4},
]

ALL_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="nested_and",
        filter={"$and": [{"$and": [{"a": 1}, {"b": 2}]}, {"c": 3}]},
        doc=DOCS,
        expected=[{"_id": 1, "a": 1, "b": 2, "c": 3}],
        msg="Nested $and matches documents satisfying all inner and outer clauses",
    ),
    QueryTestCase(
        id="three_level_nesting",
        filter={"$and": [{"$and": [{"$and": [{"a": 1}]}, {"b": 2}]}, {"c": 3}]},
        doc=DOCS,
        expected=[{"_id": 1, "a": 1, "b": 2, "c": 3}],
        msg="Three-level nested $and matches correctly",
    ),
    QueryTestCase(
        id="and_containing_or",
        filter={"$and": [{"$or": [{"a": 1}, {"a": 2}]}, {"b": 2}]},
        doc=DOCS,
        expected=[{"_id": 1, "a": 1, "b": 2, "c": 3}, {"_id": 2, "a": 2, "b": 2, "c": 3}],
        msg="$and containing $or matches docs satisfying OR and other clause",
    ),
    QueryTestCase(
        id="or_containing_and",
        filter={"$or": [{"$and": [{"a": 1}, {"b": 2}]}, {"c": 4}]},
        doc=DOCS,
        expected=[{"_id": 1, "a": 1, "b": 2, "c": 3}, {"_id": 3, "a": 1, "b": 3, "c": 4}],
        msg="$or containing $and matches docs satisfying either branch",
    ),
    QueryTestCase(
        id="and_with_nor",
        filter={"$and": [{"$nor": [{"a": 1}]}, {"b": 2}]},
        doc=DOCS,
        expected=[{"_id": 2, "a": 2, "b": 2, "c": 3}],
        msg="$and with $nor matches docs excluded by $nor and satisfying other clause",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_and_nested_logical(collection, test):
    """Test $and with nested logical operators."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg, ignore_doc_order=True)
