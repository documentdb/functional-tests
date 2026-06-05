"""Tests for multikey index creation and detection.

Validates automatic multikey detection (array field, and the scalar-to-multikey
transition on first array insert).
"""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    index_created_response,
)
from documentdb_tests.framework.assertions import (
    assertSuccess,
    assertSuccessPartial,
)
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.index


def test_multikey_creation_with_existing_array(collection):
    """Test multikey index creation succeeds when array data already exists."""
    collection.insert_one({"_id": 1, "arr": [1, 2, 3]})
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"arr": -1}, "name": "arr_neg1"}]},
    )
    assertSuccessPartial(result, index_created_response(), "Multikey index creation succeeds")


def test_multikey_array_field_is_multikey(collection):
    """Test that index on array field IS automatically multikey."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"arr": 1}, "name": "arr_1"}]},
    )
    collection.insert_one({"_id": 1, "arr": [10, 20, 30]})
    result = execute_command(
        collection, {"find": collection.name, "filter": {"arr": 20}, "hint": "arr_1"}
    )
    assertSuccess(
        result, [{"_id": 1, "arr": [10, 20, 30]}], msg="Multikey index matches array element"
    )


def test_multikey_becomes_multikey_on_first_array(collection):
    """Test that index becomes multikey when first array document is inserted."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"a": 1}, "name": "a_1"}]},
    )
    collection.insert_one({"_id": 1, "a": 5})
    collection.insert_one({"_id": 2, "a": [1, 2, 3]})
    result = execute_command(
        collection, {"find": collection.name, "filter": {"a": 2}, "hint": "a_1"}
    )
    assertSuccess(
        result, [{"_id": 2, "a": [1, 2, 3]}], msg="Index becomes multikey on array insert"
    )


def test_multikey_becomes_multikey_on_nested_array(collection):
    """Test that index becomes multikey when a nested array document is inserted."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"a": 1}, "name": "a_1"}]},
    )
    collection.insert_one({"_id": 1, "a": 5})
    collection.insert_one({"_id": 2, "a": [[1, 2], [3, 4]]})
    result = execute_command(
        collection, {"find": collection.name, "filter": {"a": [1, 2]}, "hint": "a_1"}
    )
    assertSuccess(
        result,
        [{"_id": 2, "a": [[1, 2], [3, 4]]}],
        msg="Index becomes multikey on nested array insert",
    )
