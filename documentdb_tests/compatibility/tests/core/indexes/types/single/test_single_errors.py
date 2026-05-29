"""Tests for single field index error cases.

Validates invalid sort values, field name errors, and index conflicts.
"""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    CANNOT_CREATE_INDEX_ERROR,
    INDEX_KEY_SPECS_CONFLICT_ERROR,
    INDEX_OPTIONS_CONFLICT_ERROR,
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


CONFLICT_ERROR_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="conflict_same_field_different_name",
        setup_indexes=[{"key": {"a": 1}, "name": "a_1"}],
        indexes=({"key": {"a": 1}, "name": "a_different"},),
        error_code=INDEX_OPTIONS_CONFLICT_ERROR,
        msg="Same field/order with different name should fail",
    ),
    IndexTestCase(
        id="conflict_same_name_different_field",
        setup_indexes=[{"key": {"a": 1}, "name": "my_idx"}],
        indexes=({"key": {"b": 1}, "name": "my_idx"},),
        error_code=INDEX_KEY_SPECS_CONFLICT_ERROR,
        msg="Same name with different field should fail",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CONFLICT_ERROR_TESTS))
def test_single_conflict_error(collection, test):
    """Test single field index creation conflicts."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.setup_indexes)},
    )
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    assertFailureCode(result, test.error_code, test.msg)


def test_single_option_conflict_same_key_name(collection):
    """Test recreating index with same key+name but different options fails."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"a": 1}, "name": "a_1"}]},
    )
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1", "unique": True}],
        },
    )
    assertFailureCode(
        result,
        INDEX_KEY_SPECS_CONFLICT_ERROR,
        msg="Same key+name with different options should fail",
    )
