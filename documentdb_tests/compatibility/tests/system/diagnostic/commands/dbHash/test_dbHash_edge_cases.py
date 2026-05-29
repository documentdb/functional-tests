"""Tests for dbHash command edge cases and collection variants."""

import pytest

from documentdb_tests.framework.assertions import assertProperties, assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Eq, Exists, HasKey, Includes, NotExists
from documentdb_tests.framework.target_collection import (
    CappedCollection,
    ClusteredCollection,
    NamedCollection,
    TimeseriesCollection,
    ViewCollection,
)

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


def test_dbHash_includes_system_views(database_client, collection):
    """Test dbHash includes system.views when views exist."""
    collection.insert_one({"_id": 1})
    ViewCollection().resolve(database_client, collection)
    result = execute_command(collection, {"dbHash": 1})
    assertProperties(
        result,
        {
            "collections": HasKey("system.views"),
            "uuids": HasKey("system.views"),
        },
        raw_res=True,
        msg="system.views should be included",
    )


def test_dbHash_excludes_views(database_client, collection):
    """Test dbHash excludes views from collections but includes the source."""
    collection.insert_one({"_id": 1})
    view = ViewCollection().resolve(database_client, collection)
    result = execute_command(collection, {"dbHash": 1})
    assertResult(
        result,
        expected={
            "collections": {collection.name: Exists(), view.name: NotExists()},
            "uuids": {collection.name: Exists(), view.name: NotExists()},
        },
        raw_res=True,
        msg="Views should not appear in collections",
    )


def test_dbHash_timeseries_collection(database_client, collection):
    """Test dbHash with timeseries collection includes system.buckets but not the view."""
    coll = TimeseriesCollection().resolve(database_client, collection)
    result = execute_command(coll, {"dbHash": 1})
    assertProperties(
        result,
        {
            f"collections.{coll.name}": NotExists(),
            "collections": HasKey(f"system.buckets.{coll.name}"),
        },
        raw_res=True,
        msg="Timeseries should appear as system.buckets, not as view",
    )


def test_dbHash_clustered_collection(database_client, collection):
    """Test dbHash with clustered collection treats it as a regular collection."""
    coll = ClusteredCollection().resolve(database_client, collection)
    coll.insert_one({"_id": "a", "v": 1})
    result = execute_command(coll, {"dbHash": 1})
    assertProperties(
        result,
        {
            f"collections.{coll.name}": Exists(),
            f"uuids.{coll.name}": Exists(),
        },
        raw_res=True,
        msg="Clustered collection should appear as a regular collection",
    )


def test_dbHash_nonexistent_database(database_client, collection):
    """Test dbHash on a database that does not exist returns empty collections."""
    coll = database_client[f"{collection.name}_nonexistent"]
    result = execute_command(coll, {"dbHash": 1})
    assertProperties(
        result,
        {
            "ok": Eq(1.0),
            "collections": Eq({}),
            "uuids": Eq({}),
        },
        raw_res=True,
        msg="Non-existent database should return empty collections",
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
