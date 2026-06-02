"""Tests for multikey index error cases.

Validates errors that occur when a compound index is already multikey
and a subsequent operation would create parallel arrays.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.error_codes import CANNOT_INDEX_PARALLEL_ARRAYS_ERROR
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.index


def test_multikey_rejects_parallel_array_insert(collection):
    """Verify multikey index rejects insert that would introduce parallel arrays."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1, "b": 1}, "name": "a_1_b_1"}],
        },
    )
    collection.insert_one({"_id": 1, "a": [1, 2], "b": "scalar"})
    result = execute_command(
        collection,
        {"insert": collection.name, "documents": [{"_id": 2, "a": [3, 4], "b": [5, 6]}]},
    )
    assertSuccessPartial(
        result,
        {"writeErrors": [{"code": CANNOT_INDEX_PARALLEL_ARRAYS_ERROR}]},
        msg="Insert with parallel arrays into existing multikey index should fail",
    )


def test_multikey_rejects_update_creating_parallel_arrays(collection):
    """Verify multikey index rejects update that would introduce parallel arrays."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1, "b": 1}, "name": "a_1_b_1"}],
        },
    )
    collection.insert_one({"_id": 1, "a": [1, 2], "b": "scalar"})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"b": [3, 4]}}}],
        },
    )
    assertSuccessPartial(
        result,
        {"writeErrors": [{"code": CANNOT_INDEX_PARALLEL_ARRAYS_ERROR}]},
        msg="Update creating parallel arrays on existing multikey index should fail",
    )


def test_multikey_rejects_parallel_arrays_at_build_time(collection):
    """Verify createIndexes fails when existing data has parallel arrays."""
    collection.insert_many(
        [
            {"_id": 1, "a": [1, 2], "b": "scalar"},
            {"_id": 2, "a": [3, 4], "b": [5, 6]},
        ]
    )
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1, "b": 1}, "name": "a_1_b_1"}],
        },
    )
    assertFailureCode(
        result,
        CANNOT_INDEX_PARALLEL_ARRAYS_ERROR,
        msg="Building index on data with parallel arrays should fail",
    )
