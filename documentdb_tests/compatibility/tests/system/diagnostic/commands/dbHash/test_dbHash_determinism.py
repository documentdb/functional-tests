"""Tests for dbHash determinism and consistency."""

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Eq, Ne

pytestmark = pytest.mark.admin


def test_dbHash_same_data_same_hash(collection):
    """Test same data produces same hash across multiple calls."""
    collection.insert_one({"_id": 1, "x": 1})
    r1 = execute_command(collection, {"dbHash": 1})
    r2 = execute_command(collection, {"dbHash": 1})
    hash1 = r1["collections"][collection.name]
    assertResult(
        r2,
        expected={"collections": {collection.name: Eq(hash1)}},
        raw_res=True,
        msg="Same data same hash",
    )


def test_dbHash_insert_changes_hash(collection):
    """Test inserting a document changes the collection hash."""
    collection.insert_one({"_id": 1})
    r1 = execute_command(collection, {"dbHash": 1})
    hash1 = r1["collections"][collection.name]
    collection.insert_one({"_id": 2})
    r2 = execute_command(collection, {"dbHash": 1})
    assertResult(
        r2,
        expected={"collections": {collection.name: Ne(hash1)}},
        raw_res=True,
        msg="Insert should change hash",
    )


def test_dbHash_delete_changes_hash(collection):
    """Test deleting a document changes the collection hash."""
    collection.insert_many([{"_id": 1}, {"_id": 2}])
    r1 = execute_command(collection, {"dbHash": 1})
    hash1 = r1["collections"][collection.name]
    collection.delete_one({"_id": 2})
    r2 = execute_command(collection, {"dbHash": 1})
    assertResult(
        r2,
        expected={"collections": {collection.name: Ne(hash1)}},
        raw_res=True,
        msg="Delete should change hash",
    )


def test_dbHash_update_changes_hash(collection):
    """Test updating a document changes the collection hash."""
    collection.insert_one({"_id": 1, "x": 1})
    r1 = execute_command(collection, {"dbHash": 1})
    hash1 = r1["collections"][collection.name]
    collection.update_one({"_id": 1}, {"$set": {"x": 2}})
    r2 = execute_command(collection, {"dbHash": 1})
    assertResult(
        r2,
        expected={"collections": {collection.name: Ne(hash1)}},
        raw_res=True,
        msg="Update should change hash",
    )


def test_dbHash_other_collection_unaffected(database_client):
    """Test modifying collection A does not change collection B's hash."""
    database_client["coll_a"].insert_one({"_id": 1})
    database_client["coll_b"].insert_one({"_id": 1})
    coll = database_client["coll_a"]
    r1 = execute_command(coll, {"dbHash": 1})
    hash_b = r1["collections"]["coll_b"]
    database_client["coll_a"].insert_one({"_id": 2})
    r2 = execute_command(coll, {"dbHash": 1})
    assertResult(
        r2,
        expected={"collections": {"coll_b": Eq(hash_b)}},
        raw_res=True,
        msg="coll_b hash should not change",
    )


def test_dbHash_md5_changes_when_collection_changes(collection):
    """Test md5 changes when any collection's hash changes."""
    collection.insert_one({"_id": 1})
    r1 = execute_command(collection, {"dbHash": 1})
    md5_1 = r1["md5"]
    collection.insert_one({"_id": 2})
    r2 = execute_command(collection, {"dbHash": 1})
    assertResult(r2, expected={"md5": Ne(md5_1)}, raw_res=True, msg="md5 should change")
