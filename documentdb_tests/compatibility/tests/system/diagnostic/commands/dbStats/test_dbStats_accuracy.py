"""Tests for dbStats accuracy, state changes, and field relationships.

Covers that counts reflect inserted documents, created collections, and
created indexes; that storageSize does not shrink while dataSize shrinks
after deletes; that objects equals the sum across collections; and the
fsTotalSize >= fsUsedSize relationship.
"""

import pytest
from bson import Int64

from documentdb_tests.framework.assertions import assertProperties, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Gt, Gte
from documentdb_tests.framework.target_collection import ExtraCollections

pytestmark = pytest.mark.admin


def test_dbStats_collections_count_reflects_created_collections(collection):
    """Test collections reflects the number of created collections."""
    ExtraCollections(count=3).resolve(collection.database, collection)
    result = execute_command(collection, {"dbStats": 1})
    assertSuccessPartial(
        result,
        {"collections": Int64(3)},
        msg="collections should equal the number of created collections",
    )


def test_dbStats_objects_count_equals_sum_across_collections(collection):
    """Test objects equals the sum of document counts across collections."""
    collection.insert_many([{"_id": i} for i in range(4)])
    c2 = collection.database[f"{collection.name}_c2"]
    c2.insert_many([{"_id": i} for i in range(6)])
    result = execute_command(collection, {"dbStats": 1})
    assertSuccessPartial(
        result,
        {"objects": Int64(10)},
        msg="objects should equal the total documents across all collections",
    )


def test_dbStats_indexes_count_reflects_created_indexes(collection):
    """Test indexes reflects the default _id index plus created indexes."""
    collection.insert_many([{"_id": i, "a": i, "b": i} for i in range(5)])
    collection.create_index("a")
    collection.create_index("b")
    result = execute_command(collection, {"dbStats": 1})
    assertSuccessPartial(
        result,
        {"indexes": Int64(3)},
        msg="indexes should count the default _id index plus created indexes",
    )


def test_dbStats_storage_size_does_not_decrease_after_delete(collection):
    """Test storageSize does not decrease after documents are removed."""
    collection.insert_many([{"_id": i, "data": "x" * 100} for i in range(100)])
    before = execute_command(collection, {"dbStats": 1})
    collection.delete_many({})
    after = execute_command(collection, {"dbStats": 1})
    assertProperties(
        after,
        {"storageSize": Gte(before.get("storageSize"))},
        raw_res=True,
        msg="storageSize should not decrease after deletes",
    )


def test_dbStats_data_size_decreases_after_delete(collection):
    """Test dataSize decreases after documents are removed."""
    collection.insert_many([{"_id": i, "data": "x" * 100} for i in range(100)])
    before = execute_command(collection, {"dbStats": 1})
    collection.delete_many({})
    after = execute_command(collection, {"dbStats": 1})
    assertProperties(
        before,
        {"dataSize": Gt(after.get("dataSize"))},
        raw_res=True,
        msg="dataSize should decrease after deletes",
    )


def test_dbStats_fs_total_size_gte_used_size(collection):
    """Test fsTotalSize is greater than or equal to fsUsedSize."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, {"dbStats": 1})
    assertProperties(
        result,
        {"fsTotalSize": Gte(result.get("fsUsedSize"))},
        raw_res=True,
        msg="fsTotalSize should be >= fsUsedSize",
    )
