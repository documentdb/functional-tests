"""Tests for single field index error cases.

Validates invalid sort values and field name errors.
"""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    CANNOT_CREATE_INDEX_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index

CREATION_ERROR_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="invalid_sort_zero",
        indexes=({"key": {"a": 0}, "name": "a_0"},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Sort order 0 should fail",
    ),
    IndexTestCase(
        id="invalid_dollar_prefix",
        indexes=({"key": {"$field": 1}, "name": "dollar_1"},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="$ prefix field should fail",
    ),
    IndexTestCase(
        id="invalid_empty_field",
        indexes=({"key": {"": 1}, "name": "empty_1"},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Empty field name should fail",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CREATION_ERROR_TESTS))
def test_single_creation_error(collection, test):
    """Test single field index creation with invalid arguments."""
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    assertFailureCode(result, test.error_code, test.msg)
