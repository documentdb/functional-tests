"""Tests for createIndexes field behavior and special collections.

Validates data type coverage for indexed field values, _id field index
behavior, null/missing field handling, and special collections (capped).
"""

from datetime import datetime

import pytest
from bson import Binary, Decimal128, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
    index_created_response,
)
from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index

FIELD_BEHAVIOR_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="double_values",
        doc=({"_id": 1, "a": 3.14},),
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        msg="Double values should be indexable",
    ),
    IndexTestCase(
        id="string_values",
        doc=({"_id": 1, "a": "hello"},),
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        msg="String values should be indexable",
    ),
    IndexTestCase(
        id="boolean_values",
        doc=({"_id": 1, "a": True},),
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        msg="Boolean values should be indexable",
    ),
    IndexTestCase(
        id="date_values",
        doc=({"_id": 1, "a": datetime(2024, 1, 1)},),
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        msg="Date values should be indexable",
    ),
    IndexTestCase(
        id="null_values",
        doc=({"_id": 1, "a": None},),
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        msg="Null values should be indexable",
    ),
    IndexTestCase(
        id="object_values",
        doc=({"_id": 1, "a": {"nested": 1}},),
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        msg="Object values should be indexable",
    ),
    IndexTestCase(
        id="array_values",
        doc=({"_id": 1, "a": [1, 2, 3]},),
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        msg="Array values should be indexable",
    ),
    IndexTestCase(
        id="objectid_values",
        doc=({"_id": 1, "a": ObjectId()},),
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        msg="ObjectId values should be indexable",
    ),
    IndexTestCase(
        id="decimal128_values",
        doc=({"_id": 1, "a": Decimal128("123.456")},),
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        msg="Decimal128 values should be indexable",
    ),
    IndexTestCase(
        id="bindata_values",
        doc=({"_id": 1, "a": Binary(b"\x00\x01\x02")},),
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        msg="binData values should be indexable",
    ),
    IndexTestCase(
        id="regex_values",
        doc=({"_id": 1, "a": Regex("^test", "i")},),
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        msg="Regex values should be indexable",
    ),
    IndexTestCase(
        id="timestamp_values",
        doc=({"_id": 1, "a": Timestamp(1, 1)},),
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        msg="Timestamp values should be indexable",
    ),
    IndexTestCase(
        id="minkey_values",
        doc=({"_id": 1, "a": MinKey()},),
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        msg="MinKey values should be indexable",
    ),
    IndexTestCase(
        id="maxkey_values",
        doc=({"_id": 1, "a": MaxKey()},),
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        msg="MaxKey values should be indexable",
    ),
    IndexTestCase(
        id="mixed_types",
        doc=(
            {"_id": 1, "a": 1},
            {"_id": 2, "a": "string"},
            {"_id": 3, "a": True},
            {"_id": 4, "a": None},
        ),
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        msg="Mixed types should be indexable",
    ),
    IndexTestCase(
        id="sparse_excludes_missing_field",
        doc=({"_id": 1, "a": 1}, {"_id": 2, "b": 1}),
        indexes=({"key": {"a": 1}, "name": "a_sparse", "sparse": True},),
        msg="Sparse index with missing field docs should succeed",
    ),
    IndexTestCase(
        id="ttl_null_date_field",
        doc=({"_id": 1, "a": None},),
        indexes=({"key": {"a": 1}, "name": "a_ttl", "expireAfterSeconds": 0},),
        msg="TTL on null date field should succeed",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIELD_BEHAVIOR_TESTS))
def test_createIndexes_field_behavior(collection, test):
    """Test createIndexes field behavior with various data types."""
    if test.doc:
        collection.insert_many(list(test.doc))
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": list(test.indexes),
        },
    )
    assertSuccessPartial(result, index_created_response(), test.msg)


def test_createIndexes_id_ascending_noop(database_client):
    """Test creating ascending index on _id is a no-op (default exists)."""
    coll = database_client["id_asc_test"]
    coll.drop()
    result = execute_command(
        coll,
        {
            "createIndexes": coll.name,
            "indexes": [{"key": {"_id": 1}, "name": "_id_"}],
        },
    )
    assertSuccessPartial(
        result, {"note": "all indexes already exist"}, "Ascending _id should be no-op"
    )
    coll.drop()


def test_createIndexes_id_hashed(database_client):
    """Test creating hashed index on _id succeeds."""
    coll = database_client["id_hashed_test"]
    coll.drop()
    result = execute_command(
        coll,
        {
            "createIndexes": coll.name,
            "indexes": [{"key": {"_id": "hashed"}, "name": "_id_hashed"}],
        },
    )
    assertSuccessPartial(result, index_created_response(), "Hashed _id should succeed")
    coll.drop()


def test_createIndexes_on_capped_collection(database_client):
    """Test createIndexes on capped collection succeeds."""
    database_client.drop_collection("capped_idx_test")
    database_client.create_collection("capped_idx_test", capped=True, size=4096)
    coll = database_client["capped_idx_test"]
    result = execute_command(
        coll,
        {
            "createIndexes": coll.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1"}],
        },
    )
    assertSuccessPartial(result, index_created_response(), "createIndexes on capped should succeed")
    coll.drop()
