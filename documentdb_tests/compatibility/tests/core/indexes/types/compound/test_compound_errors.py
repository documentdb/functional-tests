"""Tests for compound index error cases.

Validates error codes for invalid sort orders, naming conflicts,
and parallel arrays in compound indexes.
"""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.error_codes import (
    CANNOT_CREATE_INDEX_ERROR,
    CANNOT_INDEX_PARALLEL_ARRAYS_ERROR,
    INDEX_KEY_SPECS_CONFLICT_ERROR,
    INDEX_OPTIONS_CONFLICT_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index

COMPOUND_CREATION_ERROR_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="sort_order_zero",
        indexes=({"key": {"a": 1, "b": 0}, "name": "bad"},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Sort order 0 in compound should fail",
    ),
    IndexTestCase(
        id="sort_order_null",
        indexes=({"key": {"a": None, "b": 1}, "name": "bad"},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Sort order null in compound should fail",
    ),
    IndexTestCase(
        id="sort_order_invalid_string",
        indexes=({"key": {"a": "invalid", "b": 1}, "name": "bad"},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Invalid string sort order in compound should fail",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COMPOUND_CREATION_ERROR_TESTS))
def test_compound_creation_error(collection, test):
    """Test compound index creation error cases."""
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    assertFailureCode(result, test.error_code, test.msg)


COMPOUND_CONFLICT_ERROR_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="conflict_same_fields_different_name",
        setup_indexes=[{"key": {"a": 1, "b": 1}, "name": "idx1"}],
        indexes=({"key": {"a": 1, "b": 1}, "name": "idx2"},),
        error_code=INDEX_OPTIONS_CONFLICT_ERROR,
        msg="Same fields/order different name should fail",
    ),
    IndexTestCase(
        id="conflict_same_name_different_fields",
        setup_indexes=[{"key": {"a": 1, "b": 1}, "name": "my_idx"}],
        indexes=({"key": {"c": 1, "d": 1}, "name": "my_idx"},),
        error_code=INDEX_KEY_SPECS_CONFLICT_ERROR,
        msg="Same name different fields should fail",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COMPOUND_CONFLICT_ERROR_TESTS))
def test_compound_conflict_error(collection, test):
    """Test compound index naming conflict error cases."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.setup_indexes)},
    )
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    assertFailureCode(result, test.error_code, test.msg)


def test_compound_parallel_arrays_fail(collection):
    """Test compound index with both fields as arrays fails (parallel arrays)."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"tags": 1, "category": 1}, "name": "tags_cat"}],
        },
    )
    result = execute_command(
        collection,
        {"insert": collection.name, "documents": [{"_id": 1, "tags": [1, 2], "category": [1, 2]}]},
    )
    assertSuccessPartial(
        result,
        {"writeErrors": [{"code": CANNOT_INDEX_PARALLEL_ARRAYS_ERROR}]},
        msg="Parallel arrays should fail",
    )
