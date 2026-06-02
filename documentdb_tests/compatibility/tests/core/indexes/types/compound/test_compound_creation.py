"""Tests for compound index creation and idempotency.

Validates multi-field key creation and duplicate/ordering behavior.
"""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
    index_created_response,
)
from documentdb_tests.framework.assertions import (
    assertSuccessPartial,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index

CREATION_SUCCESS_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="creation_mixed_sort_orders",
        indexes=({"key": {"a": 1, "b": -1, "c": 1, "d": -1, "e": 1}, "name": "abcde"},),
        msg="5-field compound with mixed sort orders succeeds",
    ),
    IndexTestCase(
        id="creation_dot_notation",
        indexes=({"key": {"a.b": 1, "a.c": 1}, "name": "ab_ac"},),
        msg="Dot notation fields succeed",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CREATION_SUCCESS_TESTS))
def test_compound_creation_success(collection, test):
    """Test compound index creation success cases."""
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    assertSuccessPartial(result, index_created_response(), test.msg)


def test_compound_idempotent(collection):
    """Test creating same compound index twice is idempotent."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1, "b": 1}, "name": "a_1_b_1"}],
        },
    )
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1, "b": 1}, "name": "a_1_b_1"}],
        },
    )
    assertSuccessPartial(
        result, {"ok": 1.0, "numIndexesBefore": 2, "numIndexesAfter": 2}, msg="Duplicate is no-op"
    )


def test_compound_different_order_creates_two(collection):
    """Test same fields different order creates two separate indexes."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1, "b": 1}, "name": "a_1_b_1"}],
        },
    )
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"b": 1, "a": 1}, "name": "b_1_a_1"}],
        },
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0, "numIndexesBefore": 2, "numIndexesAfter": 3},
        msg="Different field order = separate index",
    )


def test_compound_different_sort_creates_two(collection):
    """Test same fields different sort direction creates two indexes."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1, "b": 1}, "name": "a_1_b_1"}],
        },
    )
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1, "b": -1}, "name": "a_1_b_neg1"}],
        },
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0, "numIndexesBefore": 2, "numIndexesAfter": 3},
        msg="Different sort = separate index",
    )
