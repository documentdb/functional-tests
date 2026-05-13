"""
Tests for $nor query operator argument handling.

Covers valid array argument variations: single expression, multiple expressions,
many expressions, and empty object in array.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

DOCS = [{"_id": 1, "a": 1, "b": 2}, {"_id": 2, "a": 2, "b": 1}]

VALID_ARRAY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="single_expression",
        filter={"$nor": [{"a": 1}]},
        doc=DOCS,
        expected=[{"_id": 2, "a": 2, "b": 1}],
        msg="$nor with single expression should exclude matching docs",
    ),
    QueryTestCase(
        id="two_expressions",
        filter={"$nor": [{"a": 1}, {"b": 1}]},
        doc=[{"_id": 1, "a": 1, "b": 2}, {"_id": 2, "a": 2, "b": 1}, {"_id": 3, "a": 2, "b": 2}],
        expected=[{"_id": 3, "a": 2, "b": 2}],
        msg="$nor with two expressions should return docs failing both",
    ),
    QueryTestCase(
        id="many_expressions",
        filter={"$nor": [{"a": 1}, {"b": 1}, {"a": 3}, {"b": 3}, {"a": 4}]},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2, "b": 2}],
        expected=[{"_id": 2, "a": 2, "b": 2}],
        msg="$nor with many expressions should return docs failing all",
    ),
    QueryTestCase(
        id="empty_object_in_array",
        filter={"$nor": [{}]},
        doc=DOCS,
        expected=[],
        msg="$nor with empty object matches all docs so returns empty",
    ),
]

ALL_TESTS = VALID_ARRAY_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_nor_argument_handling(collection, test):
    """Test $nor query operator argument validation."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        ignore_doc_order=True,
        msg=test.msg,
    )
