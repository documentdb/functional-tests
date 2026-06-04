"""Tests for dbHash determinism and consistency."""

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Eq, Ne
from documentdb_tests.framework.target_collection import NamedCollection

pytestmark = pytest.mark.admin


def test_dbHash_same_data_same_hash(collection):
    """Test same data produces same hash across multiple calls."""
    collection.insert_one({"_id": 1, "x": 1})
    r1 = execute_command(collection, {"dbHash": 1})
    r2 = execute_command(collection, {"dbHash": 1})
    hash1 = r1.get("collections", {}).get(collection.name, "MISSING_HASH")
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
    hash1 = r1.get("collections", {}).get(collection.name, None)
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
    hash1 = r1.get("collections", {}).get(collection.name, None)
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
    hash1 = r1.get("collections", {}).get(collection.name, None)
    collection.update_one({"_id": 1}, {"$set": {"x": 2}})
    r2 = execute_command(collection, {"dbHash": 1})
    assertResult(
        r2,
        expected={"collections": {collection.name: Ne(hash1)}},
        raw_res=True,
        msg="Update should change hash",
    )


def test_dbHash_hash_reverts_after_undo(collection):
    """Test hash returns to original after reverting data changes."""
    collection.insert_one({"_id": 1})
    r1 = execute_command(collection, {"dbHash": 1})
    hash1 = r1.get("collections", {}).get(collection.name, "MISSING_HASH")
    collection.insert_one({"_id": 2})
    collection.delete_one({"_id": 2})
    r2 = execute_command(collection, {"dbHash": 1})
    assertResult(
        r2,
        expected={"collections": {collection.name: Eq(hash1)}},
        raw_res=True,
        msg="Hash should revert after undo",
    )


def test_dbHash_other_collection_unaffected(database_client, collection):
    """Test modifying collection A does not change collection B's hash."""
    coll_a = NamedCollection(suffix="_a").resolve(database_client, collection)
    coll_b = NamedCollection(suffix="_b").resolve(database_client, collection)
    coll_a.insert_one({"_id": 1})
    coll_b.insert_one({"_id": 1})
    r1 = execute_command(coll_a, {"dbHash": 1})
    hash_b = r1.get("collections", {}).get(coll_b.name, "MISSING_HASH")
    coll_a.insert_one({"_id": 2})
    r2 = execute_command(coll_a, {"dbHash": 1})
    assertResult(
        r2,
        expected={"collections": {coll_b.name: Eq(hash_b)}},
        raw_res=True,
        msg="coll_b hash should not change",
    )


def test_dbHash_md5_changes_when_collection_changes(collection):
    """Test md5 changes when any collection's hash changes."""
    collection.insert_one({"_id": 1})
    r1 = execute_command(collection, {"dbHash": 1})
    md5_1 = r1.get("md5", None)
    collection.insert_one({"_id": 2})
    r2 = execute_command(collection, {"dbHash": 1})
    assertResult(r2, expected={"md5": Ne(md5_1)}, raw_res=True, msg="md5 should change")
