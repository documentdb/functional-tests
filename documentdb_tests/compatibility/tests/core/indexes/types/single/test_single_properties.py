"""Tests for single field index properties.

Validates NaN and Infinity handling on single field indexes.
"""

import pytest

from documentdb_tests.framework.assertions import (
    assertSuccess,
    assertSuccessNaN,
)
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.index


def test_single_nan_indexed_and_queryable(collection):
    """Test NaN in indexed field is queryable."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"a": 1}, "name": "a_1"}]},
    )
    collection.insert_one({"_id": 1, "a": float("nan")})
    result = execute_command(collection, {"find": collection.name, "filter": {"a": float("nan")}})
    assertSuccessNaN(result, [{"_id": 1, "a": float("nan")}], msg="Should find NaN document")


def test_single_infinity_indexed(collection):
    """Test Infinity in indexed field is queryable."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"a": 1}, "name": "a_1"}]},
    )
    collection.insert_one({"_id": 1, "a": float("inf")})
    result = execute_command(collection, {"find": collection.name, "filter": {"a": float("inf")}})
    assertSuccess(result, [{"_id": 1, "a": float("inf")}], msg="Should find Infinity document")


def test_single_negative_infinity_indexed(collection):
    """Test -Infinity in indexed field is queryable."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"a": 1}, "name": "a_1"}]},
    )
    collection.insert_one({"_id": 1, "a": float("-inf")})
    result = execute_command(collection, {"find": collection.name, "filter": {"a": float("-inf")}})
    assertSuccess(result, [{"_id": 1, "a": float("-inf")}], msg="Should find -Infinity document")
