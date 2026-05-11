"""Tests for listDatabases filter restricted operator errors."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR, NEAR_NOT_ALLOWED_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Filter Restricted Operator Errors]: operators that require
# capabilities unavailable in the listDatabases filter context (JS
# execution, text indexes, geospatial sorting) are rejected with an
# appropriate error.
FILTER_RESTRICTED_OPERATOR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"listDatabases": 1, "filter": {"$where": "true"}},
        error_code=BAD_VALUE_ERROR,
        msg="$where should be rejected in listDatabases filter",
        id="restricted_where",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "filter": {"$text": {"$search": "admin"}}},
        error_code=BAD_VALUE_ERROR,
        msg="$text should be rejected in listDatabases filter",
        id="restricted_text",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "filter": {"name": {"$near": [0, 0]}}},
        error_code=NEAR_NOT_ALLOWED_ERROR,
        msg="$near should be rejected in listDatabases filter",
        id="restricted_near",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "filter": {"name": {"$nearSphere": [0, 0]}}},
        error_code=NEAR_NOT_ALLOWED_ERROR,
        msg="$nearSphere should be rejected in listDatabases filter",
        id="restricted_near_sphere",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "filter": {"name": {"$geoNear": {"near": [0, 0]}}}},
        error_code=NEAR_NOT_ALLOWED_ERROR,
        msg="$geoNear should be rejected in listDatabases filter",
        id="restricted_geo_near",
    ),
]


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(FILTER_RESTRICTED_OPERATOR_TESTS))
def test_listDatabases_filter_restricted_operators(collection, test):
    """Test that restricted operators are rejected in listDatabases filter."""
    ctx = CommandContext.from_collection(collection)
    collection.database.create_collection(collection.name)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
