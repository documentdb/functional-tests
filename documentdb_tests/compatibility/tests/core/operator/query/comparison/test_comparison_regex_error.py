"""
Tests that comparison operators return BAD_VALUE when given a regex value.

Covers $ne, $gt, $gte, $lt, $lte.
"""

import pytest
from bson import Regex

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="ne_regex",
        filter={"a": {"$ne": Regex("^abc", "i")}},
        doc=[{"_id": 1, "a": "abc"}],
        error_code=BAD_VALUE_ERROR,
        msg="$ne with regex value should return BAD_VALUE",
    ),
    QueryTestCase(
        id="gt_regex",
        filter={"a": {"$gt": Regex("^abc", "i")}},
        doc=[{"_id": 1, "a": "abc"}],
        error_code=BAD_VALUE_ERROR,
        msg="$gt with regex value should return BAD_VALUE",
    ),
    QueryTestCase(
        id="gte_regex",
        filter={"a": {"$gte": Regex("^abc", "i")}},
        doc=[{"_id": 1, "a": "abc"}],
        error_code=BAD_VALUE_ERROR,
        msg="$gte with regex value should return BAD_VALUE",
    ),
    QueryTestCase(
        id="lt_regex",
        filter={"a": {"$lt": Regex("^abc", "i")}},
        doc=[{"_id": 1, "a": "abc"}],
        error_code=BAD_VALUE_ERROR,
        msg="$lt with regex value should return BAD_VALUE",
    ),
    QueryTestCase(
        id="lte_regex",
        filter={"a": {"$lte": Regex("^abc", "i")}},
        doc=[{"_id": 1, "a": "abc"}],
        error_code=BAD_VALUE_ERROR,
        msg="$lte with regex value should return BAD_VALUE",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_comparison_regex_error(collection, test):
    """Parametrized test that comparison operators reject regex values."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertFailureCode(result, test.error_code)
