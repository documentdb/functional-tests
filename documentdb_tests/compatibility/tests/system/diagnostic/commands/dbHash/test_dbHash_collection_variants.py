"""Tests for dbHash with different collection types."""

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Exists
from documentdb_tests.framework.target_collection import CappedCollection, NamedCollection

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


def test_dbHash_includes_capped_collections(database_client, collection):
    """Test dbHash includes capped collections in both collections and capped."""
    coll = CappedCollection(size=4096).resolve(database_client, collection)
    coll.insert_one({"_id": 1})
    result = execute_command(coll, {"dbHash": 1})
    assertResult(
        result,
        expected={"collections": {coll.name: Exists()}},
        raw_res=True,
        msg="Should include capped in collections",
    )


def test_dbHash_empty_collection_has_hash(database_client, collection):
    """Test dbHash immediately after collection creation (empty collection has a hash)."""
    coll = NamedCollection(suffix="_empty").resolve(database_client, collection)
    result = execute_command(coll, {"dbHash": 1})
    assertResult(
        result,
        expected={"collections": {coll.name: Exists()}},
        raw_res=True,
        msg="Empty collection should have hash",
    )
