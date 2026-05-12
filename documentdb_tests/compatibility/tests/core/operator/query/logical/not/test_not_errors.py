"""
Tests for $not query operator error cases and invalid argument handling.

Tests that $not returns correct error codes for invalid argument types,
empty objects, top-level usage, and invalid operators.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

ALL_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="not_with_plain_integer",
        filter={"val": {"$not": 5}},
        doc=[{"_id": 1, "val": 5}],
        error_code=BAD_VALUE_ERROR,
        msg="$not with plain integer should return BadValue error",
    ),
    QueryTestCase(
        id="not_with_string",
        filter={"val": {"$not": "hello"}},
        doc=[{"_id": 1, "val": 5}],
        error_code=BAD_VALUE_ERROR,
        msg="$not with string should return BadValue error",
    ),
    QueryTestCase(
        id="not_with_null",
        filter={"val": {"$not": None}},
        doc=[{"_id": 1, "val": 5}],
        error_code=BAD_VALUE_ERROR,
        msg="$not with null should return BadValue error",
    ),
    QueryTestCase(
        id="not_with_boolean",
        filter={"val": {"$not": True}},
        doc=[{"_id": 1, "val": 5}],
        error_code=BAD_VALUE_ERROR,
        msg="$not with boolean should return BadValue error",
    ),
    QueryTestCase(
        id="not_with_array",
        filter={"val": {"$not": [1, 2]}},
        doc=[{"_id": 1, "val": 5}],
        error_code=BAD_VALUE_ERROR,
        msg="$not with array should return BadValue error",
    ),
    QueryTestCase(
        id="not_with_empty_object",
        filter={"val": {"$not": {}}},
        doc=[{"_id": 1, "val": 5}],
        error_code=BAD_VALUE_ERROR,
        msg="$not with empty object should return BadValue error",
    ),
    QueryTestCase(
        id="not_at_top_level",
        filter={"$not": {"a": 1}},
        doc=[{"_id": 1, "val": 5}],
        error_code=BAD_VALUE_ERROR,
        msg="$not at top level without field should return BadValue error",
    ),
    QueryTestCase(
        id="not_with_invalid_operator",
        filter={"val": {"$not": {"$invalid": 1}}},
        doc=[{"_id": 1, "val": 5}],
        error_code=BAD_VALUE_ERROR,
        msg="$not with invalid operator inside should return BadValue error",
    ),
    QueryTestCase(
        id="not_with_where",
        filter={"val": {"$not": {"$where": "true"}}},
        doc=[{"_id": 1, "val": 5}],
        error_code=BAD_VALUE_ERROR,
        msg="$not with $where inside should return BadValue error",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_not_errors(collection, test):
    """Test $not with invalid arguments returns correct error code."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        ignore_doc_order=True,
        msg=test.msg,
    )
