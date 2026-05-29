"""Tests for dbHash command edge cases and collection variants."""

import pytest

from documentdb_tests.framework.assertions import assertProperties, assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Exists, Includes
from documentdb_tests.framework.target_collection import CappedCollection, NamedCollection

pytestmark = pytest.mark.admin


def test_dbHash_special_characters_in_name(database_client, collection):
    """Test dbHash with collection names containing special characters."""
    coll = NamedCollection(suffix="-with-dash").resolve(database_client, collection)
    coll.insert_one({"_id": 1})
    result = execute_command(coll, {"dbHash": 1})
    assertResult(
        result,
        expected={
            "collections": {coll.name: Exists()},
            "uuids": {coll.name: Exists()},
        },
        raw_res=True,
        msg="Special chars should work",
    )


def test_dbHash_many_collections(database_client, collection):
    """Test dbHash with many collections includes all."""
    colls = []
    for i in range(10):
        c = NamedCollection(suffix=f"_multi_{i}").resolve(database_client, collection)
        c.insert_one({"_id": 1})
        colls.append(c)
    result = execute_command(colls[0], {"dbHash": 1})
    assertResult(
        result,
        expected={
            "collections": {colls[0].name: Exists(), colls[9].name: Exists()},
            "uuids": {colls[0].name: Exists(), colls[9].name: Exists()},
        },
        raw_res=True,
        msg="Should include all collections",
    )


def test_dbHash_includes_capped_collections(database_client, collection):
    """Test dbHash includes capped collections in both collections and capped."""
    coll = CappedCollection(size=4096).resolve(database_client, collection)
    coll.insert_one({"_id": 1})
    result = execute_command(coll, {"dbHash": 1})
    assertProperties(
        result,
        {
            f"collections.{coll.name}": Exists(),
            f"uuids.{coll.name}": Exists(),
            "capped": Includes(coll.name),
        },
        raw_res=True,
        msg="Should include capped in both collections and capped",
    )


def test_dbHash_empty_collection_has_hash(database_client, collection):
    """Test dbHash immediately after collection creation (empty collection has a hash)."""
    coll = NamedCollection(suffix="_empty").resolve(database_client, collection)
    result = execute_command(coll, {"dbHash": 1})
    assertProperties(
        result,
        {
            f"collections.{coll.name}": Exists(),
            f"uuids.{coll.name}": Exists(),
        },
        raw_res=True,
        msg="Empty collection should have hash",
    )
