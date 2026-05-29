"""Tests for single field index creation.

Validates valid argument handling, idempotency, and duplicate prevention.
"""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
    index_created_response,
)
from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index

CREATION_SUCCESS_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="creation_ascending",
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        msg="Ascending order succeeds",
    ),
    IndexTestCase(
        id="creation_descending",
        indexes=({"key": {"a": -1}, "name": "a_neg1"},),
        msg="Descending order succeeds",
    ),
    IndexTestCase(
        id="creation_dot_notation",
        indexes=({"key": {"a.b": 1}, "name": "a.b_1"},),
        msg="Dot notation field succeeds",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CREATION_SUCCESS_TESTS))
def test_single_creation_success(collection, test):
    """Test single field index creation with valid arguments."""
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    assertSuccessPartial(result, index_created_response(), test.msg)


def test_single_creation_on_nonexistent_collection(collection):
    """Test createIndexes on non-existent collection creates collection and index."""
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"x": 1}, "name": "x_1"}]},
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0, "numIndexesBefore": 1, "numIndexesAfter": 2},
        msg="Should create collection and index",
    )


def test_single_creation_idempotent(collection):
    """Test creating same index twice is idempotent."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"a": 1}, "name": "a_1"}]},
    )
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"a": 1}, "name": "a_1"}]},
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0, "numIndexesBefore": 2, "numIndexesAfter": 2},
        msg="Duplicate index creation should be no-op",
    )


def test_single_creation_different_sort_creates_two(collection):
    """Test creating index with same field but different sort order creates two indexes."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"a": 1}, "name": "a_1"}]},
    )
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"a": -1}, "name": "a_neg1"}]},
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0, "numIndexesBefore": 2, "numIndexesAfter": 3},
        msg="Different sort order should create separate index",
    )
