"""
Tests for $nin query operator null and missing field handling.

Covers missing field exclusion, combined null with other values,
and null excluding both null and missing together.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="null_excludes_missing_field",
        filter={"x": {"$nin": [None]}},
        doc=[{"_id": 1, "y": 1}, {"_id": 2, "x": 1}],
        expected=[{"_id": 2, "x": 1}],
        msg="$nin with [null] excludes document where field is missing",
    ),
    QueryTestCase(
        id="null_and_value_excludes_null_missing_and_value",
        filter={"x": {"$nin": [None, 1]}},
        doc=[
            {"_id": 1, "x": None},
            {"_id": 2, "y": 1},
            {"_id": 3, "x": 1},
            {"_id": 4, "x": 2},
        ],
        expected=[{"_id": 4, "x": 2}],
        msg="$nin with [null, 1] excludes null, missing, and 1",
    ),
    QueryTestCase(
        id="missing_field_without_null_in_array_included",
        filter={"x": {"$nin": [1, 2]}},
        doc=[{"_id": 1, "y": 1}, {"_id": 2, "x": 1}],
        expected=[{"_id": 1, "y": 1}],
        msg="$nin without null in array does NOT exclude missing field",
    ),
    QueryTestCase(
        id="null_excludes_both_null_and_missing",
        filter={"x": {"$nin": [None]}},
        doc=[{"_id": 1, "x": None}, {"_id": 2, "y": 1}, {"_id": 3, "x": 1}],
        expected=[{"_id": 3, "x": 1}],
        msg="$nin with [null] excludes both null and missing in same query",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(TESTS))
def test_nin_null_missing(collection, test_case):
    """Parametrized test for $nin null and missing field handling."""
    collection.insert_many(test_case.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test_case.filter})
    assertSuccess(result, test_case.expected, msg=test_case.msg, ignore_doc_order=True)
