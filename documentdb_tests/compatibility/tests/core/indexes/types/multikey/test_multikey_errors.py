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


def test_multikey_rejects_update_creating_parallel_arrays_nested(collection):
    """Verify multikey index rejects update creating parallel arrays at deeper nesting level."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a.b": 1, "a.c": 1}, "name": "ab_1_ac_1"}],
        },
    )
    collection.insert_one({"_id": 1, "a": {"b": [1, 2], "c": "scalar"}})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a.c": [3, 4]}}}],
        },
    )
    assertSuccessPartial(
        result,
        {"writeErrors": [{"code": CANNOT_INDEX_PARALLEL_ARRAYS_ERROR}]},
        msg="Update creating parallel arrays at nested level should fail",
    )


def test_multikey_rejects_update_creating_parallel_arrays_deeply_nested(collection):
    """Verify multikey index rejects update creating parallel arrays at deeply nested level."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a.b.c": 1, "a.b.d": 1}, "name": "abc_1_abd_1"}],
        },
    )
    collection.insert_one({"_id": 1, "a": {"b": {"c": [1, 2], "d": "scalar"}}})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a.b.d": [3, 4]}}}],
        },
    )
    assertSuccessPartial(
        result,
        {"writeErrors": [{"code": CANNOT_INDEX_PARALLEL_ARRAYS_ERROR}]},
        msg="Update creating parallel arrays at deeply nested level should fail",
    )


def test_multikey_allows_alternating_array_fields(collection):
    """Verify multikey index allows inserts where different fields are arrays in different docs."""
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
        {"insert": collection.name, "documents": [{"_id": 2, "a": "scalar", "b": [3, 4]}]},
    )
    assertSuccessPartial(
        result,
        {"n": 1},
        msg="Insert with array in alternate field should succeed",
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
