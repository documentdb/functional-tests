"""
Tests for $in query operator null and missing field handling.

Covers null matching, missing field matching, null vs falsy value distinction,
and combined null with other values.
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
        id="null_matches_null_field",
        filter={"x": {"$in": [None]}},
        doc=[{"_id": 1, "x": None}, {"_id": 2, "x": 1}],
        expected=[{"_id": 1, "x": None}],
        msg="$in with [null] matches document where field is null",
    ),
    QueryTestCase(
        id="null_matches_missing_field",
        filter={"x": {"$in": [None]}},
        doc=[{"_id": 1, "y": 1}, {"_id": 2, "x": 1}],
        expected=[{"_id": 1, "y": 1}],
        msg="$in with [null] matches document where field is missing",
    ),
    QueryTestCase(
        id="null_skips_int_zero",
        filter={"x": {"$in": [None]}},
        doc=[{"_id": 1, "x": 0}, {"_id": 2, "x": None}],
        expected=[{"_id": 2, "x": None}],
        msg="$in with [null] does NOT match int 0",
    ),
    QueryTestCase(
        id="null_skips_bool_false",
        filter={"x": {"$in": [None]}},
        doc=[{"_id": 1, "x": False}, {"_id": 2, "x": None}],
        expected=[{"_id": 2, "x": None}],
        msg="$in with [null] does NOT match bool false",
    ),
    QueryTestCase(
        id="null_skips_empty_string",
        filter={"x": {"$in": [None]}},
        doc=[{"_id": 1, "x": ""}, {"_id": 2, "x": None}],
        expected=[{"_id": 2, "x": None}],
        msg="$in with [null] does NOT match empty string",
    ),
    QueryTestCase(
        id="null_and_value_matches_null_missing_and_value",
        filter={"x": {"$in": [None, 1]}},
        doc=[
            {"_id": 1, "x": None},
            {"_id": 2, "y": 1},
            {"_id": 3, "x": 1},
            {"_id": 4, "x": 2},
        ],
        expected=[{"_id": 1, "x": None}, {"_id": 2, "y": 1}, {"_id": 3, "x": 1}],
        msg="$in with [null, 1] matches null, missing, and 1",
    ),
    QueryTestCase(
        id="missing_field_no_null_in_array",
        filter={"x": {"$in": [1, 2]}},
        doc=[{"_id": 1, "y": 1}, {"_id": 2, "x": 1}],
        expected=[{"_id": 2, "x": 1}],
        msg="$in without null in array does NOT match missing field",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(TESTS))
def test_in_null_missing(collection, test_case):
    """Parametrized test for $in null and missing field handling."""
    collection.insert_many(test_case.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test_case.filter})
    assertSuccess(result, test_case.expected, msg=test_case.msg, ignore_doc_order=True)
