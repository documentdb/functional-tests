"""Tests for dbHash with different collection types."""

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Exists

pytestmark = pytest.mark.admin


def test_dbHash_includes_regular_collections(collection):
    """Test dbHash includes regular collections."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, {"dbHash": 1})
    assertResult(
        result,
        expected={"collections": {collection.name: Exists()}},
        raw_res=True,
        msg="Should include regular collection",
    )


def test_dbHash_includes_capped_collections(database_client):
    """Test dbHash includes capped collections in both collections and capped."""
    database_client.create_collection("capped_hash", capped=True, size=4096)
    database_client["capped_hash"].insert_one({"_id": 1})
    coll = database_client["capped_hash"]
    result = execute_command(coll, {"dbHash": 1})
    assertResult(
        result,
        expected={"collections": {"capped_hash": Exists()}},
        raw_res=True,
        msg="Should include capped in collections",
    )


def test_dbHash_empty_collection_has_hash(database_client):
    """Test dbHash immediately after collection creation (empty collection has a hash)."""
    database_client.create_collection("empty_hash_coll")
    coll = database_client["empty_hash_coll"]
    result = execute_command(coll, {"dbHash": 1})
    assertResult(
        result,
        expected={"collections": {"empty_hash_coll": Exists()}},
        raw_res=True,
        msg="Empty collection should have hash",
    )
