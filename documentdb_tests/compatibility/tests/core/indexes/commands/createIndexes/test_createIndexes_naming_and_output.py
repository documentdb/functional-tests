"""Tests for createIndexes naming, output fields, and idempotency.

Validates name auto-generation, output fields
(numIndexesBefore, numIndexesAfter, createdCollectionAutomatically, note),
no-op behavior, and drop/recreate behavior.
"""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
    index_created_response,
)
from documentdb_tests.framework.assertions import (
    assertSuccess,
    assertSuccessPartial,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index

NAMING_AND_OUTPUT_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="name_with_spaces",
        indexes=({"key": {"a": 1}, "name": "my index name"},),
        msg="Name with spaces should succeed",
    ),
    IndexTestCase(
        id="name_with_dots",
        indexes=({"key": {"a": 1}, "name": "my.index.name"},),
        msg="Name with dots should succeed",
    ),
    IndexTestCase(
        id="name_with_unicode",
        indexes=({"key": {"a": 1}, "name": "índex_naïve_über"},),
        msg="Name with unicode should succeed",
    ),
    IndexTestCase(
        id="name_with_special_chars",
        indexes=({"key": {"a": 1}, "name": "idx-a_1@v2#test"},),
        msg="Name with special chars should succeed",
    ),
    IndexTestCase(
        id="long_name",
        indexes=({"key": {"a": 1}, "name": "a" * 128},),
        msg="Long name should succeed",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NAMING_AND_OUTPUT_TESTS))
def test_createIndexes_naming_and_output(collection, test):
    """Test createIndexes naming and output patterns."""
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": list(test.indexes),
        },
    )
    assertSuccessPartial(result, index_created_response(), test.msg)


def test_createIndexes_auto_name_single_asc(database_client):
    """Test auto-generated name for {a: 1} is a_1."""
    coll = database_client["auto_name_test"]
    coll.drop()
    result = execute_command(
        coll,
        {
            "createIndexes": coll.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1"}],
        },
    )
    assertSuccessPartial(result, {"ok": 1.0}, "Index with name a_1 should succeed")
    coll.drop()


def test_createIndexes_auto_name_compound(database_client):
    """Test auto-generated name for {a: 1, b: -1} is a_1_b_-1."""
    coll = database_client["auto_name_compound_test"]
    coll.drop()
    result = execute_command(
        coll,
        {
            "createIndexes": coll.name,
            "indexes": [{"key": {"a": 1, "b": -1}, "name": "a_1_b_-1"}],
        },
    )
    assertSuccessPartial(result, {"ok": 1.0}, "Index with name a_1_b_-1 should succeed")
    coll.drop()


def test_createIndexes_auto_name_nested_field(database_client):
    """Test auto-generated name for {'a.b': 1} is a.b_1."""
    coll = database_client["auto_name_nested_test"]
    coll.drop()
    result = execute_command(
        coll,
        {
            "createIndexes": coll.name,
            "indexes": [{"key": {"a.b": 1}, "name": "a.b_1"}],
        },
    )
    assertSuccessPartial(result, {"ok": 1.0}, "Index with name a.b_1 should succeed")
    coll.drop()


def test_createIndexes_auto_name_hashed(database_client):
    """Test auto-generated name for {a: 'hashed'} is a_hashed."""
    coll = database_client["auto_name_hashed_test"]
    coll.drop()
    result = execute_command(
        coll,
        {
            "createIndexes": coll.name,
            "indexes": [{"key": {"a": "hashed"}, "name": "a_hashed"}],
        },
    )
    assertSuccessPartial(result, {"ok": 1.0}, "Index with name a_hashed should succeed")
    coll.drop()


def test_createIndexes_same_key_same_name_noop(collection):
    """Test creating same index with same name again is a no-op."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "idx_a"}],
        },
    )
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "idx_a"}],
        },
    )
    assertSuccessPartial(
        result, {"note": "all indexes already exist"}, "Same key+name should be no-op"
    )


def test_createIndexes_num_indexes_before_includes_id(collection):
    """Test numIndexesBefore reflects count including _id index."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1"}],
        },
    )
    assertSuccess(
        result,
        {"numIndexesBefore": 1, "numIndexesAfter": 2, "ok": 1.0},
        raw_res=True,
        transform=lambda r: {
            "numIndexesBefore": r["numIndexesBefore"],
            "numIndexesAfter": r["numIndexesAfter"],
            "ok": r["ok"],
        },
    )


def test_createIndexes_num_indexes_after_increments(collection):
    """Test numIndexesAfter = numIndexesBefore + number of new indexes."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"a": 1}, "name": "a_1"},
                {"key": {"b": 1}, "name": "b_1"},
            ],
        },
    )
    assertSuccess(
        result,
        {"numIndexesBefore": 1, "numIndexesAfter": 3, "ok": 1.0},
        raw_res=True,
        transform=lambda r: {
            "numIndexesBefore": r["numIndexesBefore"],
            "numIndexesAfter": r["numIndexesAfter"],
            "ok": r["ok"],
        },
    )


def test_createIndexes_created_collection_automatically_true(database_client):
    """Test createdCollectionAutomatically:true when collection didn't exist."""
    coll = database_client["new_coll_output_test"]
    coll.drop()
    result = execute_command(
        coll,
        {
            "createIndexes": coll.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1"}],
        },
    )
    assertSuccessPartial(
        result, {"createdCollectionAutomatically": True}, "Should report collection auto-created"
    )
    coll.drop()


def test_createIndexes_created_collection_automatically_false(collection):
    """Test createdCollectionAutomatically:false when collection existed."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1"}],
        },
    )
    assertSuccessPartial(
        result,
        {"createdCollectionAutomatically": False},
        "Should report collection not auto-created",
    )


def test_createIndexes_noop_num_indexes_unchanged(collection):
    """Test numIndexesBefore == numIndexesAfter when index already exists."""
    collection.insert_one({"_id": 1})
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1"}],
        },
    )
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1"}],
        },
    )
    assertSuccess(
        result,
        {"numIndexesBefore": 2, "numIndexesAfter": 2, "ok": 1.0},
        raw_res=True,
        transform=lambda r: {
            "numIndexesBefore": r["numIndexesBefore"],
            "numIndexesAfter": r["numIndexesAfter"],
            "ok": r["ok"],
        },
    )


def test_createIndexes_mixed_existing_and_new(collection):
    """Test creating indexes where one already exists and one is new."""
    collection.insert_one({"_id": 1})
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1"}],
        },
    )
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"a": 1}, "name": "a_1"},
                {"key": {"b": 1}, "name": "b_1"},
            ],
        },
    )
    assertSuccess(
        result,
        {"numIndexesBefore": 2, "numIndexesAfter": 3, "ok": 1.0},
        raw_res=True,
        transform=lambda r: {
            "numIndexesBefore": r["numIndexesBefore"],
            "numIndexesAfter": r["numIndexesAfter"],
            "ok": r["ok"],
        },
    )


def test_createIndexes_three_indexes_single_command(collection):
    """Test creating 3 indexes in one command succeeds."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"a": 1}, "name": "a_1"},
                {"key": {"b": 1}, "name": "b_1"},
                {"key": {"c": 1}, "name": "c_1"},
            ],
        },
    )
    assertSuccess(
        result,
        {"numIndexesBefore": 1, "numIndexesAfter": 4, "ok": 1.0},
        raw_res=True,
        transform=lambda r: {
            "numIndexesBefore": r["numIndexesBefore"],
            "numIndexesAfter": r["numIndexesAfter"],
            "ok": r["ok"],
        },
    )


def test_createIndexes_on_nonexistent_db_auto_creates(database_client):
    """Test createIndex on non-existent database auto-creates database and collection."""
    coll = database_client["auto_create_db_test"]
    coll.drop()
    result = execute_command(
        coll,
        {
            "createIndexes": coll.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1"}],
        },
    )
    assertSuccess(
        result,
        {"numIndexesBefore": 1, "numIndexesAfter": 2, "ok": 1.0},
        raw_res=True,
        transform=lambda r: {
            "numIndexesBefore": r["numIndexesBefore"],
            "numIndexesAfter": r["numIndexesAfter"],
            "ok": r["ok"],
        },
    )
    coll.drop()


def test_createIndexes_id_on_nonexistent_collection_noop(database_client):
    """Test createIndex on _id field alone on non-existent collection is a no-op."""
    coll = database_client["id_noop_test"]
    coll.drop()
    result = execute_command(
        coll,
        {
            "createIndexes": coll.name,
            "indexes": [{"key": {"_id": 1}, "name": "_id_"}],
        },
    )
    assertSuccessPartial(
        result, {"note": "all indexes already exist"}, "Creating _id index should be no-op"
    )
    coll.drop()


def test_createIndexes_drop_and_recreate_same_spec(database_client):
    """Test dropping and recreating index with same spec succeeds."""
    coll = database_client["drop_recreate_test"]
    coll.drop()
    execute_command(
        coll,
        {
            "createIndexes": coll.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1"}],
        },
    )
    execute_command(coll, {"dropIndexes": coll.name, "index": "a_1"})
    result = execute_command(
        coll,
        {
            "createIndexes": coll.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1"}],
        },
    )
    assertSuccessPartial(result, {"ok": 1.0}, "Recreate after drop should succeed")
    coll.drop()


def test_createIndexes_drop_and_recreate_different_name(database_client):
    """Test dropping index and recreating with different name but same key succeeds."""
    coll = database_client["drop_recreate_name_test"]
    coll.drop()
    execute_command(
        coll,
        {
            "createIndexes": coll.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1"}],
        },
    )
    execute_command(coll, {"dropIndexes": coll.name, "index": "a_1"})
    result = execute_command(
        coll,
        {
            "createIndexes": coll.name,
            "indexes": [{"key": {"a": 1}, "name": "a_new_name"}],
        },
    )
    assertSuccessPartial(result, {"ok": 1.0}, "Recreate with different name should succeed")
    coll.drop()


def test_createIndexes_drop_and_recreate_different_key(database_client):
    """Test dropping index and recreating with same name but different key succeeds."""
    coll = database_client["drop_recreate_key_test"]
    coll.drop()
    execute_command(
        coll,
        {
            "createIndexes": coll.name,
            "indexes": [{"key": {"a": 1}, "name": "my_idx"}],
        },
    )
    execute_command(coll, {"dropIndexes": coll.name, "index": "my_idx"})
    result = execute_command(
        coll,
        {
            "createIndexes": coll.name,
            "indexes": [{"key": {"b": 1}, "name": "my_idx"}],
        },
    )
    assertSuccessPartial(result, {"ok": 1.0}, "Recreate with different key should succeed")
    coll.drop()


def test_createIndexes_ns_field_in_listIndexes(database_client):
    """Test that ns field in listIndexes output matches db.collection."""
    coll = database_client["ns_field_test"]
    coll.drop()
    execute_command(
        coll,
        {
            "createIndexes": coll.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1"}],
        },
    )
    result = execute_command(coll, {"listIndexes": coll.name})
    expected_ns = f"{database_client.name}.{coll.name}"
    assertSuccess(
        result,
        expected_ns,
        msg="ns field should match db.collection",
        raw_res=True,
        transform=lambda r: next(
            (idx["ns"] for idx in r["cursor"]["firstBatch"] if "ns" in idx), expected_ns
        ),
    )
    coll.drop()
