"""
Tests for $elemMatch error cases.

Covers invalid argument types passed to $elemMatch and bare top-level usage.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

INVALID_ARGUMENT_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="integer_argument",
        filter={"a": {"$elemMatch": 1}},
        doc=[{"_id": 1, "a": [1]}],
        error_code=BAD_VALUE_ERROR,
        msg="Integer argument should fail",
    ),
    QueryTestCase(
        id="null_argument",
        filter={"a": {"$elemMatch": None}},
        doc=[{"_id": 1, "a": [1]}],
        error_code=BAD_VALUE_ERROR,
        msg="Null argument should fail",
    ),
    QueryTestCase(
        id="array_argument",
        filter={"a": {"$elemMatch": [1]}},
        doc=[{"_id": 1, "a": [1]}],
        error_code=BAD_VALUE_ERROR,
        msg="Array argument should fail",
    ),
    QueryTestCase(
        id="string_argument",
        filter={"a": {"$elemMatch": "a"}},
        doc=[{"_id": 1, "a": [1]}],
        error_code=BAD_VALUE_ERROR,
        msg="String argument should fail",
    ),
    QueryTestCase(
        id="boolean_argument",
        filter={"a": {"$elemMatch": True}},
        doc=[{"_id": 1, "a": [1]}],
        error_code=BAD_VALUE_ERROR,
        msg="Boolean argument should fail",
    ),
    QueryTestCase(
        id="double_argument",
        filter={"a": {"$elemMatch": 3.14}},
        doc=[{"_id": 1, "a": [1]}],
        error_code=BAD_VALUE_ERROR,
        msg="Double argument should fail",
    ),
    QueryTestCase(
        id="top_level_bare_usage",
        filter={"$elemMatch": {"$gt": 1}},
        doc=[{"_id": 1, "a": [1]}],
        error_code=BAD_VALUE_ERROR,
        msg="Bare $elemMatch at top level without field should fail",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_ARGUMENT_TESTS))
def test_elemMatch_query_errors(collection, test):
    """Test $elemMatch query error cases."""
    collection.insert_many(test.doc)
    result = execute_command(
        collection,
        {"find": collection.name, "filter": test.filter},
    )
    assertFailureCode(result, test.error_code)
